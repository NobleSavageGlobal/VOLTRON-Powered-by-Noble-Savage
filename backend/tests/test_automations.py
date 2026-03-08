from __future__ import annotations

import pytest
from httpx import AsyncClient


async def _auth(client: AsyncClient, suffix: str) -> dict:
    """Register, login, return headers."""
    email = f"auto_{suffix}@example.com"
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "SecurePass123!",
            "full_name": "Auto User",
            "org_name": f"Auto Org {suffix}",
        },
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "SecurePass123!"},
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_list_workflows_empty(client: AsyncClient) -> None:
    headers = await _auth(client, "wf_empty")
    resp = await client.get("/api/v1/automations/workflows", headers=headers)
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_create_workflow(client: AsyncClient) -> None:
    headers = await _auth(client, "wf_create")
    resp = await client.post(
        "/api/v1/automations/workflows",
        headers=headers,
        json={
            "name": "Auto-classify uploads",
            "trigger_type": "document_uploaded",
            "trigger_config": {"doc_types": ["bank_statement"]},
            "actions": [{"type": "classify", "model": "gpt-4o"}],
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Auto-classify uploads"
    assert data["trigger_type"] == "document_uploaded"
    assert data["status"] == "active"


@pytest.mark.asyncio
async def test_update_workflow(client: AsyncClient) -> None:
    headers = await _auth(client, "wf_update")
    create_resp = await client.post(
        "/api/v1/automations/workflows",
        headers=headers,
        json={
            "name": "Original Name",
            "trigger_type": "schedule",
            "trigger_config": {},
            "actions": [],
        },
    )
    wf_id = create_resp.json()["id"]

    resp = await client.patch(
        f"/api/v1/automations/workflows/{wf_id}",
        headers=headers,
        json={"name": "Updated Name", "status": "paused"},
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Updated Name"
    assert resp.json()["status"] == "paused"


@pytest.mark.asyncio
async def test_list_runs_empty(client: AsyncClient) -> None:
    headers = await _auth(client, "runs")
    resp = await client.get("/api/v1/automations/runs", headers=headers)
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_list_events_empty(client: AsyncClient) -> None:
    headers = await _auth(client, "events")
    resp = await client.get("/api/v1/automations/events", headers=headers)
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_automations_requires_auth(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/automations/workflows")
    assert resp.status_code == 401
