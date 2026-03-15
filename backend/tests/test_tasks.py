from __future__ import annotations

import pytest
from httpx import AsyncClient


async def _get_auth_headers(client: AsyncClient, suffix: str = "") -> dict:
    email = f"taskuser{suffix}@example.com"
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "SecurePass123!",
            "full_name": "Task User",
            "org_name": f"Task Org {suffix}",
        },
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "SecurePass123!"},
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_create_task(client: AsyncClient) -> None:
    headers = await _get_auth_headers(client, "create")
    response = await client.post(
        "/api/v1/tasks/",
        headers=headers,
        json={"title": "Test Task", "priority": "high"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Task"
    assert data["priority"] == "high"


@pytest.mark.asyncio
async def test_list_tasks(client: AsyncClient) -> None:
    headers = await _get_auth_headers(client, "listx")
    response = await client.get("/api/v1/tasks/", headers=headers)
    assert response.status_code == 200
    assert "items" in response.json()


@pytest.mark.asyncio
async def test_update_task(client: AsyncClient) -> None:
    headers = await _get_auth_headers(client, "update")
    create_resp = await client.post(
        "/api/v1/tasks/",
        headers=headers,
        json={"title": "Update Me"},
    )
    task_id = create_resp.json()["id"]
    response = await client.patch(
        f"/api/v1/tasks/{task_id}",
        headers=headers,
        json={"status": "done"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "done"
