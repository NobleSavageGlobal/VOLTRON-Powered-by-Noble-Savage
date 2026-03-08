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
        files={
            "file": ("test_invoice.pdf", io.BytesIO(file_content), "application/pdf")
        },
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
        files={
            "file": ("contract.pdf", io.BytesIO(b"contract content"), "application/pdf")
        },
    )
    doc_id = upload_resp.json()["id"]

    response = await client.get(f"/api/v1/documents/{doc_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["id"] == doc_id


@pytest.mark.asyncio
async def test_documents_require_auth(client: AsyncClient) -> None:
    response = await client.get("/api/v1/documents/")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_batch_upload_auto_onboard_reuses_client(client: AsyncClient) -> None:
    headers = await _get_auth_headers(client, "batch")
    files = [
        (
            "files",
            (
                "client_profile.txt",
                io.BytesIO(
                    b"Business Name: Atlas Ventures LLC\nIndustry: Technology\nRevenue: $325,000\n"
                ),
                "text/plain",
            ),
        ),
        (
            "files",
            (
                "invoice_001.txt",
                io.BytesIO(b"Invoice\nCustomer: Atlas Ventures LLC\nTotal: $12,500\n"),
                "text/plain",
            ),
        ),
    ]
    response = await client.post(
        "/api/v1/documents/upload/batch",
        headers=headers,
        data={"auto_onboard": "true"},
        files=files,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["success_count"] == 2
    assert data["failure_count"] == 0

    client_ids = {
        item["document"]["client_id"] for item in data["items"] if item.get("document")
    }
    assert len(client_ids) == 1
    assert None not in client_ids


@pytest.mark.asyncio
async def test_auto_onboard_existing_document(client: AsyncClient) -> None:
    headers = await _get_auth_headers(client, "manual-onboard")
    upload_resp = await client.post(
        "/api/v1/documents/upload",
        headers=headers,
        files={
            "file": (
                "onboard.txt",
                io.BytesIO(b"Company Name: Noble Logistics LLC\n"),
                "text/plain",
            )
        },
    )
    assert upload_resp.status_code == 201
    doc_id = upload_resp.json()["id"]
    assert upload_resp.json()["client_id"] is None

    onboard_resp = await client.post(
        f"/api/v1/documents/{doc_id}/auto-onboard", headers=headers
    )
    assert onboard_resp.status_code == 200
    onboarded = onboard_resp.json()
    assert onboarded["client_id"] is not None
    assert onboarded["extracted_data"]["onboarding"]["auto_onboarded"] is True
