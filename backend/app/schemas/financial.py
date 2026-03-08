from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class FinancialConnectionCreate(BaseModel):
    client_id: uuid.UUID
    provider: str
    account_mask: str | None = None


class FinancialConnectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    client_id: uuid.UUID
    provider: str
    account_mask: str | None
    status: str
    last_synced_at: datetime | None
    created_at: datetime


class TransactionCreate(BaseModel):
    account_id: uuid.UUID
    posted_at: datetime
    amount: float
    description: str
    merchant: str | None = None
    category: str | None = None
    transaction_type: str
    raw_json: dict | None = None


class TransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    account_id: uuid.UUID
    posted_at: datetime
    amount: Any
    description: str
    merchant: str | None
    category: str | None
    transaction_type: str
    hash_dedupe: str
    created_at: datetime


class MonthlyRollupResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    client_id: uuid.UUID
    period_month: Any
    income_total: Any
    expense_total: Any
    net_total: Any
    category_breakdown: dict | None
    created_at: datetime
    updated_at: datetime


class ObligationCreate(BaseModel):
    client_id: uuid.UUID
    obligation_type: str
    creditor_name: str | None = None
    principal: float | None = None
    monthly_payment: float | None = None
    apr: float | None = None
    balance: float | None = None
    status: str = "current"
    notes: str | None = None


class ObligationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    client_id: uuid.UUID
    obligation_type: str
    creditor_name: str | None
    principal: Any
    monthly_payment: Any
    apr: Any
    balance: Any
    status: str
    notes: str | None
    created_at: datetime
    updated_at: datetime


class FinancialSummaryResponse(BaseModel):
    client_id: uuid.UUID
    total_income_3mo: float
    total_expenses_3mo: float
    net_3mo: float
    avg_monthly_income: float
    avg_monthly_expenses: float
    obligations_count: int
    obligations_total_monthly: float
    recent_rollups: list[MonthlyRollupResponse]
