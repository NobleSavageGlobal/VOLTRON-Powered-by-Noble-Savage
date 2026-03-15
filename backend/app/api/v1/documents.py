from __future__ import annotations

import uuid

from fastapi import APIRouter, File, Form, Query, UploadFile
from sqlalchemy import func, select

from app.api.deps import DB, CurrentUser
from app.core.exceptions import ForbiddenError, NotFoundError, ValidationError
from app.models.document import Document
from app.schemas.document import (
    DocumentBatchUploadResponse,
    DocumentListResponse,
    DocumentResponse,
    DocumentUpdate,
    DocumentUploadResult,
)
from app.services.document_service import DocumentService

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentResponse, status_code=201)
async def upload_document(
    current_user: CurrentUser,
    db: DB,
    file: UploadFile = File(...),
    auto_onboard: bool = Form(False),
    client_id: uuid.UUID | None = Form(None),
) -> Document:
    if not current_user.org_id:
        raise ForbiddenError("You must belong to an organization to upload documents")

    service = DocumentService(db)
    document = await service.create_document(
        file=file,
        user=current_user,
        client_id=client_id,
        auto_onboard=auto_onboard,
    )
    return document


@router.post(
    "/upload/batch", response_model=DocumentBatchUploadResponse, status_code=201
)
async def upload_documents_batch(
    current_user: CurrentUser,
    db: DB,
    files: list[UploadFile] = File(...),
    auto_onboard: bool = Form(False),
    client_id: uuid.UUID | None = Form(None),
) -> DocumentBatchUploadResponse:
    if not current_user.org_id:
        raise ForbiddenError("You must belong to an organization to upload documents")
    if not files:
        raise ValidationError("At least one file is required")

    service = DocumentService(db)
    items: list[DocumentUploadResult] = []
    resolved_client_id = client_id
    for file in files:
        try:
            document = await service.create_document(
                file=file,
                user=current_user,
                client_id=resolved_client_id,
                auto_onboard=auto_onboard,
            )
            if auto_onboard and resolved_client_id is None and document.client_id:
                resolved_client_id = document.client_id
            items.append(
                DocumentUploadResult(
                    filename=file.filename or document.original_filename,
                    success=True,
                    document=document,
                )
            )
        except Exception as exc:
            items.append(
                DocumentUploadResult(
                    filename=file.filename or "upload",
                    success=False,
                    error=str(exc),
                )
            )

    success_count = len([item for item in items if item.success])
    failure_count = len(items) - success_count
    return DocumentBatchUploadResponse(
        items=items,
        success_count=success_count,
        failure_count=failure_count,
    )


@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    current_user: CurrentUser,
    db: DB,
    status: str | None = Query(None),
    doc_type: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> DocumentListResponse:
    if not current_user.org_id:
        return DocumentListResponse(items=[], total=0, page=page, page_size=page_size)

    query = select(Document).where(Document.org_id == current_user.org_id)
    if status:
        query = query.where(Document.status == status)
    if doc_type:
        query = query.where(Document.doc_type == doc_type)

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar_one()

    query = (
        query.order_by(Document.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(query)
    items = list(result.scalars().all())

    return DocumentListResponse(
        items=items, total=total, page=page, page_size=page_size
    )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: uuid.UUID,
    current_user: CurrentUser,
    db: DB,
) -> Document:
    result = await db.execute(
        select(Document).where(
            Document.id == document_id, Document.org_id == current_user.org_id
        )
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise NotFoundError("Document", str(document_id))
    return doc


@router.patch("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: uuid.UUID,
    payload: DocumentUpdate,
    current_user: CurrentUser,
    db: DB,
) -> Document:
    result = await db.execute(
        select(Document).where(
            Document.id == document_id, Document.org_id == current_user.org_id
        )
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise NotFoundError("Document", str(document_id))

    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(doc, field, value)

    await db.commit()
    await db.refresh(doc)
    return doc


@router.delete("/{document_id}", status_code=204)
async def delete_document(
    document_id: uuid.UUID,
    current_user: CurrentUser,
    db: DB,
) -> None:
    result = await db.execute(
        select(Document).where(
            Document.id == document_id, Document.org_id == current_user.org_id
        )
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise NotFoundError("Document", str(document_id))
    await db.delete(doc)
    await db.commit()


@router.post("/{document_id}/reprocess", response_model=DocumentResponse)
async def reprocess_document(
    document_id: uuid.UUID,
    current_user: CurrentUser,
    db: DB,
) -> Document:
    result = await db.execute(
        select(Document).where(
            Document.id == document_id, Document.org_id == current_user.org_id
        )
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise NotFoundError("Document", str(document_id))

    service = DocumentService(db)
    doc = await service.reprocess_document(doc)
    return doc


@router.post("/{document_id}/auto-onboard", response_model=DocumentResponse)
async def auto_onboard_document(
    document_id: uuid.UUID,
    current_user: CurrentUser,
    db: DB,
    client_id: uuid.UUID | None = Query(None),
) -> Document:
    result = await db.execute(
        select(Document).where(
            Document.id == document_id, Document.org_id == current_user.org_id
        )
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise NotFoundError("Document", str(document_id))

    service = DocumentService(db)
    client = await service.auto_onboard_document(
        doc=doc, user=current_user, client_id=client_id
    )
    current_data = (
        dict(doc.extracted_data) if isinstance(doc.extracted_data, dict) else {}
    )
    current_data["onboarding"] = {
        "auto_onboarded": True,
        "client_id": str(client.id),
        "client_name": client.display_name,
    }
    doc.extracted_data = current_data
    await db.commit()
    await db.refresh(doc)
    return doc
