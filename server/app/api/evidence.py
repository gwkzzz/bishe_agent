from __future__ import annotations

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, require_case_for_user
from app.core.database import get_db
from app.integrations.errors import ObjectStorageError, QueuePublishError
from app.integrations.minio_client import MinIOClient
from app.integrations.rabbitmq import RabbitMQPublisher
from app.integrations.redis_client import RedisClient
from app.models import AsyncTask, EvidenceItem, LegalCase, User
from app.schemas.cases import EvidenceItemRead
from app.schemas.evidence import AnalyzeEvidenceResponse, EvidenceUploadResponse, TaskRead

router = APIRouter(tags=["evidence"])


@router.post(
    "/api/evidence/upload",
    response_model=EvidenceUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
def upload_evidence(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    case_id: Annotated[str, Form()],
    file: Annotated[UploadFile, File()],
    name: Annotated[str | None, Form()] = None,
    evidence_type: Annotated[str | None, Form()] = None,
) -> EvidenceItem:
    require_case_for_user(case_id, current_user, db)
    evidence = EvidenceItem(
        case_id=case_id,
        name=(name or file.filename or "未命名证据").strip(),
        evidence_type=evidence_type,
        confirmed_by_user=False,
    )
    db.add(evidence)
    db.flush()

    filename = Path(file.filename or "upload.bin").name
    object_name = f"cases/{case_id}/evidence/{evidence.id}/{filename}"
    try:
        file.file.seek(0, 2)
        length = file.file.tell()
        file.file.seek(0)
        evidence.file_url = MinIOClient().put_object(
            object_name=object_name,
            data=file.file,
            length=length,
            content_type=file.content_type or "application/octet-stream",
        )
    except ObjectStorageError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Object storage upload failed.",
        ) from exc

    db.commit()
    db.refresh(evidence)
    return evidence


@router.post("/api/evidence/{evidence_id}/analyze", response_model=AnalyzeEvidenceResponse)
async def analyze_evidence(
    evidence_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> AnalyzeEvidenceResponse:
    evidence = _get_evidence_for_user(evidence_id, current_user, db)
    task = AsyncTask(
        case_id=evidence.case_id,
        evidence_id=evidence.id,
        task_type="evidence_analyze",
        status="pending",
        progress=0,
        retry_count=0,
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    redis = RedisClient()
    publisher = RabbitMQPublisher()
    try:
        await redis.set_json(
            f"task:{task.id}",
            {"task_id": task.id, "status": task.status, "progress": task.progress},
            ttl_seconds=60 * 60,
        )
        await publisher.declare_queue("evidence.analyze")
        await publisher.publish_json(
            "evidence.analyze",
            {
                "task_id": task.id,
                "case_id": evidence.case_id,
                "evidence_id": evidence.id,
                "file_url": evidence.file_url,
            },
        )
    except (QueuePublishError, Exception) as exc:
        task.status = "failed"
        task.error_message = str(exc)
        db.add(task)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to publish evidence analysis task.",
        ) from exc
    finally:
        await redis.close()
        await publisher.close()

    return AnalyzeEvidenceResponse(task_id=task.id, evidence_id=evidence.id, status=task.status)


@router.get("/api/tasks/{task_id}", response_model=TaskRead)
def get_task(
    task_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> AsyncTask:
    task = db.scalar(
        select(AsyncTask)
        .join(LegalCase, LegalCase.id == AsyncTask.case_id)
        .where(AsyncTask.id == task_id, LegalCase.user_id == current_user.id)
    )
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")
    return task


@router.get("/api/cases/{case_id}/evidence", response_model=list[EvidenceItemRead])
def list_case_evidence(
    case_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[EvidenceItem]:
    require_case_for_user(case_id, current_user, db)
    return list(
        db.scalars(
            select(EvidenceItem)
            .where(EvidenceItem.case_id == case_id)
            .order_by(EvidenceItem.created_at.asc())
        )
    )


def _get_evidence_for_user(evidence_id: str, current_user: User, db: Session) -> EvidenceItem:
    evidence = db.scalar(
        select(EvidenceItem)
        .join(LegalCase, LegalCase.id == EvidenceItem.case_id)
        .where(EvidenceItem.id == evidence_id, LegalCase.user_id == current_user.id)
    )
    if evidence is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found.")
    return evidence
