from __future__ import annotations

import pytest
from httpx import AsyncClient


async def _auth(client: AsyncClient, suffix: str) -> tuple[dict, str]:
    """Register, login, create a client, return (headers, client_id)."""
    email = f"fin_{suffix}@example.com"
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "SecurePass123!",
            "full_name": "Fin User",
            "org_name": f"Fin Org {suffix}",
        },
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "SecurePass123!"},
    )
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    cr = await client.post(
        "/api/v1/clients/",
        headers=headers,
        json={"display_name": f"Client {suffix}", "entity_type": "person"},
    )
    return headers, cr.json()["id"]


@pytest.mark.asyncio
async def test_list_connections_empty(client: AsyncClient) -> None:
    headers, cid = await _auth(client, "conn_empty")
    resp = await client.get(
        "/api/v1/financial/connections", headers=headers, params={"client_id": cid}
    )
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_create_and_list_connection(client: AsyncClient) -> None:
    headers, cid = await _auth(client, "conn_create")
    resp = await client.post(
        "/api/v1/financial/connections",
        headers=headers,
        json={"client_id": cid, "provider": "plaid", "account_mask": "1234"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["provider"] == "plaid"
    assert data["account_mask"] == "1234"

    # List should include the connection
    list_resp = await client.get(
        "/api/v1/financial/connections", headers=headers, params={"client_id": cid}
    )
    assert len(list_resp.json()) >= 1


@pytest.mark.asyncio
async def test_list_obligations_empty(client: AsyncClient) -> None:
    headers, cid = await _auth(client, "obl_empty")
    resp = await client.get(
        "/api/v1/financial/obligations", headers=headers, params={"client_id": cid}
    )
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_create_obligation(client: AsyncClient) -> None:
    headers, cid = await _auth(client, "obl_create")
    resp = await client.post(
        "/api/v1/financial/obligations",
        headers=headers,
        json={
            "client_id": cid,
            "obligation_type": "mortgage",
            "creditor_name": "Big Bank",
            "principal": 200000,
            "monthly_payment": 1200,
            "apr": 5.5,
            "balance": 195000,
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["obligation_type"] == "mortgage"
    assert data["creditor_name"] == "Big Bank"


@pytest.mark.asyncio
async def test_financial_summary(client: AsyncClient) -> None:
    headers, cid = await _auth(client, "fin_summary")
    resp = await client.get(
        "/api/v1/financial/summary", headers=headers, params={"client_id": cid}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "total_income_3mo" in data
    assert "obligations_count" in data


@pytest.mark.asyncio
async def test_rollups_empty(client: AsyncClient) -> None:
    headers, cid = await _auth(client, "rollups")
    resp = await client.get(
        "/api/v1/financial/rollups", headers=headers, params={"client_id": cid}
    )
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_transactions_empty(client: AsyncClient) -> None:
    headers, cid = await _auth(client, "txn")
    resp = await client.get(
        "/api/v1/financial/transactions", headers=headers, params={"client_id": cid}
    )
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_financial_requires_auth(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/financial/connections")
    assert resp.status_code == 401
