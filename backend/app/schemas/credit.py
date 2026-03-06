from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class CreditReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    client_id: uuid.UUID
    source: str
    report_date: Any
    status: str
    bureaus: list | None
    created_at: datetime
    tradelines_count: int = 0
    collections_count: int = 0


class TradelineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    credit_report_id: uuid.UUID
    creditor_name: str
    account_type: str
    balance: Any
    credit_limit: Any
    payment_status: str | None
    opened_at: Any
    closed_at: Any
    utilization: Any
    created_at: datetime


class CollectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    credit_report_id: uuid.UUID
    collector_name: str | None
    original_creditor: str | None
    amount: Any
    opened_at: Any
    status: str | None
    created_at: datetime


class DisputeCreate(BaseModel):
    bureau: str
    furnisher: str | None = None
    issue_type: str
    notes_json: dict | None = None


class DisputeUpdate(BaseModel):
    status: str | None = None
    notes_json: dict | None = None
    sent_at: datetime | None = None
    expected_response_by: Any = None
    resolved_at: datetime | None = None


class DisputeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    client_id: uuid.UUID
    bureau: str
    furnisher: str | None
    issue_type: str
    status: str
    created_at: datetime
    sent_at: datetime | None
    expected_response_by: Any
    resolved_at: datetime | None
    notes_json: dict | None


class DisputeLetterCreate(BaseModel):
    dispute_id: uuid.UUID
    content_text: str
    template_version: str = "1.0"


class DisputeLetterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    dispute_id: uuid.UUID
    template_version: str
    content_text: str
    created_by: uuid.UUID
    created_at: datetime
