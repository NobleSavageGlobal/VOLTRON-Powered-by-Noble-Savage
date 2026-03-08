from __future__ import annotations

import pytest
from httpx import AsyncClient


async def _auth(client: AsyncClient, suffix: str) -> dict:
    """Register, login, return headers."""
    email = f"know_{suffix}@example.com"
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "SecurePass123!",
            "full_name": "Knowledge User",
            "org_name": f"Know Org {suffix}",
        },
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "SecurePass123!"},
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_search_requires_query(client: AsyncClient) -> None:
    headers = await _auth(client, "search_q")
    resp = await client.get("/api/v1/knowledge/search", headers=headers)
    assert resp.status_code == 422  # missing required `q` parameter


@pytest.mark.asyncio
async def test_search_returns_list(client: AsyncClient) -> None:
    headers = await _auth(client, "search_list")
    resp = await client.get(
        "/api/v1/knowledge/search", headers=headers, params={"q": "taxes"}
    )
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_list_chunks_empty(client: AsyncClient) -> None:
    headers = await _auth(client, "chunks")
    resp = await client.get("/api/v1/knowledge/chunks", headers=headers)
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_knowledge_requires_auth(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/knowledge/search", params={"q": "test"})
    assert resp.status_code == 401
