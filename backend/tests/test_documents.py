from __future__ import annotations

import io

import pytest
from httpx import AsyncClient


async def _get_auth_headers(client: AsyncClient, suffix: str = "") -> dict:
    email = f"docuser{suffix}@example.com"
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "SecurePass123!",
            "full_name": "Doc User",
            "org_name": f"Doc Org {suffix}",
        },
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "SecurePass123!"},
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_upload_document(client: AsyncClient) -> None:
    headers = await _get_auth_headers(client, "upload")
    file_content = b"%PDF-1.4 fake pdf content for testing"
    response = await client.post(
        "/api/v1/documents/upload",
        headers=headers,
        files={"file": ("test_invoice.pdf", io.BytesIO(file_content), "application/pdf")},
    )
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["original_filename"] == "test_invoice.pdf"
    assert data["mime_type"] == "application/pdf"


@pytest.mark.asyncio
async def test_list_documents(client: AsyncClient) -> None:
    headers = await _get_auth_headers(client, "list")
    response = await client.get("/api/v1/documents/", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_get_document(client: AsyncClient) -> None:
    headers = await _get_auth_headers(client, "get")
    upload_resp = await client.post(
        "/api/v1/documents/upload",
        headers=headers,
        files={"file": ("contract.pdf", io.BytesIO(b"contract content"), "application/pdf")},
    )
    doc_id = upload_resp.json()["id"]

    response = await client.get(f"/api/v1/documents/{doc_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["id"] == doc_id


@pytest.mark.asyncio
async def test_documents_require_auth(client: AsyncClient) -> None:
    response = await client.get("/api/v1/documents/")
    assert response.status_code == 401
