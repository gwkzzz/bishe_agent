from __future__ import annotations

from datetime import date
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.dependencies import get_current_user, require_case_for_user
from app.core.database import get_db
from app.models import CaseFact, EvidenceItem, LegalCase, ProfileCandidate, User
from app.schemas.cases import (
    CaseCreate,
    CaseDetailRead,
    CaseRead,
    CaseUpdate,
    ConfirmProfileRequest,
    ConfirmProfileResponse,
)

router = APIRouter(prefix="/api/cases", tags=["cases"])


@router.get("", response_model=list[CaseRead])
def list_cases(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[LegalCase]:
    return list(
        db.scalars(
            select(LegalCase)
            .where(LegalCase.user_id == current_user.id)
            .order_by(LegalCase.updated_at.desc(), LegalCase.created_at.desc())
        )
    )


@router.post("", response_model=CaseRead, status_code=status.HTTP_201_CREATED)
def create_case(
    payload: CaseCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> LegalCase:
    case = LegalCase(
        user_id=current_user.id,
        title=payload.title.strip(),
        domain=payload.domain,
        cause=payload.cause,
        status="open",
        summary=payload.summary,
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    return case


@router.get("/{case_id}", response_model=CaseDetailRead)
def get_case(
    case_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> LegalCase:
    case = db.scalar(
        select(LegalCase)
        .options(
            selectinload(LegalCase.facts),
            selectinload(LegalCase.evidence_items),
            selectinload(LegalCase.generated_documents),
            selectinload(LegalCase.profile_candidates),
        )
        .where(LegalCase.id == case_id, LegalCase.user_id == current_user.id)
    )
    if case is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found.")
    return case


@router.patch("/{case_id}", response_model=CaseRead)
def update_case(
    case_id: str,
    payload: CaseUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> LegalCase:
    case = require_case_for_user(case_id, current_user, db)
    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(case, key, value.strip() if isinstance(value, str) else value)
    db.add(case)
    db.commit()
    db.refresh(case)
    return case


@router.post("/{case_id}/confirm-profile", response_model=ConfirmProfileResponse)
def confirm_profile_candidate(
    case_id: str,
    payload: ConfirmProfileRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ConfirmProfileResponse:
    require_case_for_user(case_id, current_user, db)
    candidate = db.get(ProfileCandidate, payload.candidate_id)
    if candidate is None or candidate.case_id != case_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile candidate not found.")

    candidate.status = payload.status
    created_resource_id: str | None = None
    if payload.status == "confirmed":
        created_resource_id = _materialize_candidate(candidate, db)

    db.add(candidate)
    db.commit()
    db.refresh(candidate)
    return ConfirmProfileResponse(candidate=candidate, created_resource_id=created_resource_id)


def _materialize_candidate(candidate: ProfileCandidate, db: Session) -> str | None:
    content = _content_dict(candidate.content_json)
    if candidate.candidate_type == "fact":
        fact = CaseFact(
            case_id=candidate.case_id,
            fact_text=str(content.get("fact_text") or content.get("fact") or ""),
            occurred_at=_parse_date(content.get("occurred_at") or content.get("time")),
            source=str(content.get("source") or "profile_candidate"),
            confidence=_parse_float(content.get("confidence")),
            confirmed_by_user=True,
        )
        if not fact.fact_text:
            return None
        db.add(fact)
        db.flush()
        return fact.id

    if candidate.candidate_type == "evidence":
        evidence = EvidenceItem(
            case_id=candidate.case_id,
            name=str(content.get("name") or "待补充证据"),
            evidence_type=content.get("evidence_type") or content.get("type"),
            file_url=content.get("file_url"),
            extracted_text=content.get("extracted_text"),
            proves=content.get("proves"),
            strength=content.get("strength"),
            risk=content.get("risk"),
            confirmed_by_user=True,
        )
        db.add(evidence)
        db.flush()
        return evidence.id

    return None


def _content_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _parse_date(value: Any) -> date | None:
    if isinstance(value, date):
        return value
    if isinstance(value, str) and value:
        try:
            return date.fromisoformat(value[:10])
        except ValueError:
            return None
    return None


def _parse_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
