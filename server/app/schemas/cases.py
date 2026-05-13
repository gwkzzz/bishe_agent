from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class CaseCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    domain: str = Field(default="labor_dispute", max_length=64)
    cause: str | None = Field(default=None, max_length=128)
    summary: str | None = None


class CaseUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    cause: str | None = Field(default=None, max_length=128)
    status: str | None = Field(default=None, max_length=64)
    summary: str | None = None
    confidence: float | None = None


class CaseFactRead(BaseModel):
    id: str
    fact_text: str
    occurred_at: date | None
    source: str | None
    confidence: float | None
    confirmed_by_user: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class EvidenceItemRead(BaseModel):
    id: str
    case_id: str
    name: str
    evidence_type: str | None
    file_url: str | None
    extracted_text: str | None
    proves: str | None
    strength: str | None
    risk: str | None
    confirmed_by_user: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class GeneratedDocumentRead(BaseModel):
    id: str
    case_id: str
    document_type: str
    title: str
    content_md: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProfileCandidateRead(BaseModel):
    id: str
    case_id: str
    candidate_type: str
    content_json: dict[str, Any]
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CaseRead(BaseModel):
    id: str
    user_id: str
    title: str
    domain: str
    cause: str | None
    status: str
    summary: str | None
    confidence: float | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CaseDetailRead(CaseRead):
    facts: list[CaseFactRead] = []
    evidence_items: list[EvidenceItemRead] = []
    generated_documents: list[GeneratedDocumentRead] = []
    profile_candidates: list[ProfileCandidateRead] = []


class ConfirmProfileRequest(BaseModel):
    candidate_id: str
    status: Literal["confirmed", "rejected"]


class ConfirmProfileResponse(BaseModel):
    candidate: ProfileCandidateRead
    created_resource_id: str | None = None
