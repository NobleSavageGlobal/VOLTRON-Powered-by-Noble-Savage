from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.models.financial import (
    FinancialAccount,
    FinancialConnection,
    MonthlyRollup,
    Obligation,
    Transaction,
)

logger = get_logger(__name__)


class FinancialService:
    async def create_connection(
        self,
        db: AsyncSession,
        org_id: uuid.UUID,
        client_id: uuid.UUID,
        provider: str,
        account_mask: str | None,
    ) -> FinancialConnection:
        conn = FinancialConnection(
            org_id=org_id,
            client_id=client_id,
            provider=provider,
            account_mask=account_mask,
            status="active",
        )
        db.add(conn)
        await db.flush()
        await db.refresh(conn)
        return conn

    async def simulate_plaid_sync(
        self, db: AsyncSession, connection_id: uuid.UUID
    ) -> dict:
        result = await db.execute(
            select(FinancialConnection).where(FinancialConnection.id == connection_id)
        )
        conn = result.scalar_one_or_none()
        if not conn:
            raise NotFoundError("FinancialConnection", str(connection_id))

        account = FinancialAccount(
            connection_id=connection_id,
            account_mask="0000",
            account_type="checking",
            name="Mock Checking",
            currency="USD",
            current_balance=Decimal("5000.00"),
        )
        db.add(account)
        await db.flush()

        transactions_created = 0
        mock_data = [
            ("credit", Decimal("3000.00"), "Payroll deposit", "income"),
            ("debit", Decimal("500.00"), "Rent payment", "housing"),
            ("debit", Decimal("200.00"), "Grocery store", "food"),
        ]
        for t_type, amount, desc, category in mock_data:
            raw = f"{connection_id}{desc}{amount}"
            h = hashlib.sha256(raw.encode()).hexdigest()
            existing = await db.execute(
                select(Transaction).where(Transaction.hash_dedupe == h)
            )
            if existing.scalar_one_or_none() is None:
                txn = Transaction(
                    account_id=account.id,
                    posted_at=datetime.now(timezone.utc),
                    amount=amount,
                    description=desc,
                    category=category,
                    transaction_type=t_type,
                    hash_dedupe=h,
                )
                db.add(txn)
                transactions_created += 1

        conn.last_synced_at = datetime.now(timezone.utc)
        await db.flush()
        return {
            "transactions_created": transactions_created,
            "connection_id": str(connection_id),
        }

    async def get_transactions(
        self, db: AsyncSession, client_id: uuid.UUID, limit: int = 50, offset: int = 0
    ) -> list[Transaction]:
        stmt = (
            select(Transaction)
            .join(FinancialAccount, Transaction.account_id == FinancialAccount.id)
            .join(
                FinancialConnection,
                FinancialAccount.connection_id == FinancialConnection.id,
            )
            .where(FinancialConnection.client_id == client_id)
            .order_by(Transaction.posted_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def compute_monthly_rollups(
        self, db: AsyncSession, client_id: uuid.UUID
    ) -> list[MonthlyRollup]:
        transactions = await self.get_transactions(db, client_id, limit=1000)
        monthly: dict[str, dict] = {}
        for txn in transactions:
            key = (
                txn.posted_at.strftime("%Y-%m-01")
                if hasattr(txn.posted_at, "strftime")
                else str(txn.posted_at)[:7] + "-01"
            )
            if key not in monthly:
                monthly[key] = {
                    "income": Decimal("0"),
                    "expense": Decimal("0"),
                    "breakdown": {},
                }
            amt = Decimal(str(txn.amount))
            if txn.transaction_type == "credit":
                monthly[key]["income"] += amt
            else:
                monthly[key]["expense"] += amt
            cat = txn.category or "other"
            monthly[key]["breakdown"][cat] = float(
                Decimal(str(monthly[key]["breakdown"].get(cat, 0))) + amt
            )

        rollups = []
        for period, data in monthly.items():
            existing = await db.execute(
                select(MonthlyRollup).where(
                    MonthlyRollup.client_id == client_id,
                    MonthlyRollup.period_month == period,
                )
            )
            rollup = existing.scalar_one_or_none()
            net = data["income"] - data["expense"]
            if rollup:
                rollup.income_total = data["income"]
                rollup.expense_total = data["expense"]
                rollup.net_total = net
                rollup.category_breakdown = data["breakdown"]
            else:
                rollup = MonthlyRollup(
                    client_id=client_id,
                    period_month=period,
                    income_total=data["income"],
                    expense_total=data["expense"],
                    net_total=net,
                    category_breakdown=data["breakdown"],
                )
                db.add(rollup)
            await db.flush()
            rollups.append(rollup)
        return rollups

    async def get_financial_summary(
        self, db: AsyncSession, client_id: uuid.UUID
    ) -> dict:
        rollups = await self.compute_monthly_rollups(db, client_id)
        recent = sorted(rollups, key=lambda r: str(r.period_month), reverse=True)[:3]
        total_income = sum(float(r.income_total) for r in recent)
        total_expenses = sum(float(r.expense_total) for r in recent)
        months = len(recent) or 1
        obligations = await self.list_obligations(db, client_id)
        total_monthly = sum(float(o.monthly_payment or 0) for o in obligations)
        return {
            "client_id": client_id,
            "total_income_3mo": total_income,
            "total_expenses_3mo": total_expenses,
            "net_3mo": total_income - total_expenses,
            "avg_monthly_income": total_income / months,
            "avg_monthly_expenses": total_expenses / months,
            "obligations_count": len(obligations),
            "obligations_total_monthly": total_monthly,
            "recent_rollups": recent,
        }

    async def create_obligation(
        self, db: AsyncSession, client_id: uuid.UUID, data: dict
    ) -> Obligation:
        data.pop("client_id", None)
        ob = Obligation(client_id=client_id, **data)
        db.add(ob)
        await db.flush()
        await db.refresh(ob)
        return ob

    async def list_obligations(
        self, db: AsyncSession, client_id: uuid.UUID
    ) -> list[Obligation]:
        result = await db.execute(
            select(Obligation).where(Obligation.client_id == client_id)
        )
        return list(result.scalars().all())


financial_service = FinancialService()
