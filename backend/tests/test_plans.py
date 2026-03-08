from __future__ import annotations

import pytest
from httpx import AsyncClient


async def _auth(client: AsyncClient, suffix: str) -> tuple[dict, str]:
    """Register, login, create a client, return (headers, client_id)."""
    email = f"plan_{suffix}@example.com"
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "SecurePass123!",
            "full_name": "Plan User",
            "org_name": f"Plan Org {suffix}",
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
        json={"display_name": f"Client {suffix}", "entity_type": "business"},
    )
    return headers, cr.json()["id"]


@pytest.mark.asyncio
async def test_list_plans_empty(client: AsyncClient) -> None:
    headers, cid = await _auth(client, "plans_empty")
    resp = await client.get(
        "/api/v1/plans/", headers=headers, params={"client_id": cid}
    )
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_scores_latest(client: AsyncClient) -> None:
    headers, cid = await _auth(client, "scores")
    resp = await client.get(
        "/api/v1/plans/scores/latest", headers=headers, params={"client_id": cid}
    )
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_plans_requires_auth(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/plans/", params={"client_id": "fake"})
    assert resp.status_code == 401
