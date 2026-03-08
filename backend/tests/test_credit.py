from __future__ import annotations

import pytest
from httpx import AsyncClient


async def _auth(client: AsyncClient, suffix: str) -> tuple[dict, str]:
    """Register, login, create a client, return (headers, client_id)."""
    email = f"credit_{suffix}@example.com"
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "SecurePass123!",
            "full_name": "Credit User",
            "org_name": f"Credit Org {suffix}",
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
async def test_list_reports_empty(client: AsyncClient) -> None:
    headers, cid = await _auth(client, "rpt_empty")
    resp = await client.get(
        "/api/v1/credit/reports", headers=headers, params={"client_id": cid}
    )
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_list_disputes_empty(client: AsyncClient) -> None:
    headers, cid = await _auth(client, "disp_empty")
    resp = await client.get(
        "/api/v1/credit/disputes", headers=headers, params={"client_id": cid}
    )
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_create_dispute(client: AsyncClient) -> None:
    headers, cid = await _auth(client, "disp_create")
    resp = await client.post(
        "/api/v1/credit/disputes",
        headers=headers,
        json={
            "client_id": cid,
            "bureau": "experian",
            "issue_type": "incorrect_balance",
            "furnisher": "Big Lender",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["bureau"] == "experian"
    assert data["issue_type"] == "incorrect_balance"
    assert data["status"] == "draft"


@pytest.mark.asyncio
async def test_update_dispute(client: AsyncClient) -> None:
    headers, cid = await _auth(client, "disp_upd")
    create_resp = await client.post(
        "/api/v1/credit/disputes",
        headers=headers,
        json={"client_id": cid, "bureau": "equifax", "issue_type": "not_mine"},
    )
    dispute_id = create_resp.json()["id"]

    resp = await client.patch(
        f"/api/v1/credit/disputes/{dispute_id}",
        headers=headers,
        json={"status": "sent"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "sent"


@pytest.mark.asyncio
async def test_credit_health(client: AsyncClient) -> None:
    headers, cid = await _auth(client, "health")
    resp = await client.get(
        "/api/v1/credit/health", headers=headers, params={"client_id": cid}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "derogatory_count" in data
    assert "utilization_avg" in data
    assert "collection_total" in data


@pytest.mark.asyncio
async def test_credit_requires_auth(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/credit/reports", params={"client_id": "fake"})
    assert resp.status_code == 401
