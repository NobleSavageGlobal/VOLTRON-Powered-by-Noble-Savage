from __future__ import annotations

import pytest
from httpx import AsyncClient


async def _get_auth_headers(client: AsyncClient, suffix: str = "") -> dict:
    email = f"clientuser{suffix}@example.com"
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "SecurePass123!",
            "full_name": "Client User",
            "org_name": f"Client Org {suffix}",
        },
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "SecurePass123!"},
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_create_client(client: AsyncClient) -> None:
    headers = await _get_auth_headers(client, "create")
    response = await client.post(
        "/api/v1/clients/",
        headers=headers,
        json={
            "display_name": "Acme Corp",
            "entity_type": "business",
            "industry": "Technology",
            "annual_revenue_range": "$100K–$250K",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["display_name"] == "Acme Corp"
    assert data["entity_type"] == "business"
    assert data["industry"] == "Technology"
    assert data["status"] == "active"


@pytest.mark.asyncio
async def test_list_clients(client: AsyncClient) -> None:
    headers = await _get_auth_headers(client, "list")
    # Create a client first
    await client.post(
        "/api/v1/clients/",
        headers=headers,
        json={"display_name": "List Test Client", "entity_type": "person"},
    )
    response = await client.get("/api/v1/clients/", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any(c["display_name"] == "List Test Client" for c in data)


@pytest.mark.asyncio
async def test_get_client(client: AsyncClient) -> None:
    headers = await _get_auth_headers(client, "get")
    create_resp = await client.post(
        "/api/v1/clients/",
        headers=headers,
        json={"display_name": "Get Test Client", "entity_type": "business"},
    )
    created_client_id = create_resp.json()["id"]

    response = await client.get(f"/api/v1/clients/{created_client_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["id"] == created_client_id
    assert response.json()["display_name"] == "Get Test Client"


@pytest.mark.asyncio
async def test_update_client(client: AsyncClient) -> None:
    headers = await _get_auth_headers(client, "update")
    create_resp = await client.post(
        "/api/v1/clients/",
        headers=headers,
        json={"display_name": "Update Me", "entity_type": "person"},
    )
    created_client_id = create_resp.json()["id"]

    response = await client.patch(
        f"/api/v1/clients/{created_client_id}",
        headers=headers,
        json={"display_name": "Updated Name", "industry": "Finance"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["display_name"] == "Updated Name"
    assert data["industry"] == "Finance"


@pytest.mark.asyncio
async def test_deactivate_client(client: AsyncClient) -> None:
    headers = await _get_auth_headers(client, "deactivate")
    create_resp = await client.post(
        "/api/v1/clients/",
        headers=headers,
        json={"display_name": "Deactivate Me", "entity_type": "person"},
    )
    created_client_id = create_resp.json()["id"]

    # DELETE soft-deactivates the client
    response = await client.delete(f"/api/v1/clients/{created_client_id}", headers=headers)
    assert response.status_code == 204

    # Client still exists but is inactive
    get_resp = await client.get(f"/api/v1/clients/{created_client_id}", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["status"] == "inactive"


@pytest.mark.asyncio
async def test_clients_require_auth(client: AsyncClient) -> None:
    response = await client.get("/api/v1/clients/")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_clients_status_filter(client: AsyncClient) -> None:
    headers = await _get_auth_headers(client, "filter")
    # Create two clients
    resp1 = await client.post(
        "/api/v1/clients/",
        headers=headers,
        json={"display_name": "Active Client", "entity_type": "person"},
    )
    resp2 = await client.post(
        "/api/v1/clients/",
        headers=headers,
        json={"display_name": "To Deactivate", "entity_type": "person"},
    )
    client2_id = resp2.json()["id"]
    # Deactivate the second
    await client.delete(f"/api/v1/clients/{client2_id}", headers=headers)

    # Filter active only
    active_resp = await client.get("/api/v1/clients/?status=active", headers=headers)
    assert active_resp.status_code == 200
    active_names = [c["display_name"] for c in active_resp.json()]
    assert "Active Client" in active_names
    assert "To Deactivate" not in active_names
