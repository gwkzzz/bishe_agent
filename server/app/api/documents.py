from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.integrations.algorithm_client import AlgorithmClient
from app.integrations.errors import AlgorithmClientError
from app.models import GeneratedDocument, LegalCase, User
from app.schemas.documents import ArbitrationDocumentRequest, ArbitrationDocumentResponse

router = APIRouter(tags=["documents"])


@router.post("/api/documents/arbitration", response_model=ArbitrationDocumentResponse)
async def create_arbitration_document(
    payload: ArbitrationDocumentRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> GeneratedDocument:
    case = db.scalar(
        select(LegalCase)
        .options(selectinload(LegalCase.facts), selectinload(LegalCase.evidence_items))
        .where(LegalCase.id == payload.case_id, LegalCase.user_id == current_user.id)
    )
    if case is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found.")

    algorithm_payload = {
        "case_id": case.id,
        "summary": case.summary,
        "cause": case.cause,
        "facts": [fact.fact_text for fact in case.facts],
        "evidence": [evidence.name for evidence in case.evidence_items],
    }
    try:
        result = await AlgorithmClient().generate_arbitration_document(
            algorithm_payload,
            trace_id="document-generation",
        )
    except AlgorithmClientError:
        result = _fallback_document(case)

    document = GeneratedDocument(
        case_id=case.id,
        document_type="arbitration",
        title=str(result.get("title") or "劳动仲裁申请书初稿"),
        content_md=str(result.get("content_md") or result.get("content") or ""),
        status=str(result.get("status") or "draft"),
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


@router.get("/api/documents/{document_id}", response_model=ArbitrationDocumentResponse)
def get_document(
    document_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> GeneratedDocument:
    document = db.scalar(
        select(GeneratedDocument)
        .join(LegalCase, LegalCase.id == GeneratedDocument.case_id)
        .where(GeneratedDocument.id == document_id, LegalCase.user_id == current_user.id)
    )
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")
    return document


def _fallback_document(case: LegalCase) -> dict[str, Any]:
    return {
        "title": "劳动仲裁申请书初稿",
        "content_md": "\n".join(
            [
                "# 劳动仲裁申请书",
                "",
                "## 申请人",
                "待补充",
                "",
                "## 被申请人",
                "待补充",
                "",
                "## 仲裁请求",
                "待补充",
                "",
                "## 事实与理由",
                case.summary or "待补充",
                "",
                "## 证据目录",
                "待补充",
                "",
                "## 风险提示",
                "本初稿仅供参考，提交前需要由专业人士复核。",
            ]
        ),
        "status": "draft",
    }
