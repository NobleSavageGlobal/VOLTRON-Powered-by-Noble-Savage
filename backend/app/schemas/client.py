from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ClientCreate(BaseModel):
    display_name: str
    entity_type: str = "person"
    industry: str | None = None
    annual_revenue_range: str | None = None
    profile_json: dict | None = None


class ClientUpdate(BaseModel):
    display_name: str | None = None
    entity_type: str | None = None
    industry: str | None = None
    annual_revenue_range: str | None = None
    profile_json: dict | None = None
    status: str | None = None


class ClientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    org_id: uuid.UUID
    display_name: str
    entity_type: str
    industry: str | None
    annual_revenue_range: str | None
    profile_json: dict | None
    status: str
    created_at: datetime
    updated_at: datetime
