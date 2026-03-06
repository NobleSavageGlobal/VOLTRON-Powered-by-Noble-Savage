from __future__ import annotations

import pytest
from httpx import AsyncClient


async def _get_auth_headers(client: AsyncClient, suffix: str = "") -> dict:
    email = f"orguser{suffix}@example.com"
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "SecurePass123!",
            "full_name": "Org User",
            "org_name": f"Org Test {suffix}",
        },
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "SecurePass123!"},
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_get_my_org(client: AsyncClient) -> None:
    headers = await _get_auth_headers(client, "getme")
    response = await client.get("/api/v1/organizations/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["name"] == "Org Test getme"


@pytest.mark.asyncio
async def test_get_org_requires_auth(client: AsyncClient) -> None:
    response = await client.get("/api/v1/organizations/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_org_members(client: AsyncClient) -> None:
    headers = await _get_auth_headers(client, "members")
    response = await client.get("/api/v1/organizations/me/members", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    emails = [m["email"] for m in data]
    assert "orgusermembers@example.com" in emails


@pytest.mark.asyncio
async def test_update_org_as_admin(client: AsyncClient) -> None:
    # Register with explicit admin role to be allowed to update the org
    email = "orgadminupdate@example.com"
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "SecurePass123!",
            "full_name": "Admin User",
            "org_name": "Admin Org",
            "role": "admin",
        },
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "SecurePass123!"},
    )
    headers = {"Authorization": f"Bearer {resp.json()['access_token']}"}

    response = await client.patch(
        "/api/v1/organizations/me",
        headers=headers,
        json={"name": "Updated Org Name"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Org Name"
