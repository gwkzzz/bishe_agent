from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, require_case_for_user
from app.core.database import SessionLocal, get_db
from app.integrations.algorithm_client import AlgorithmClient
from app.integrations.errors import AlgorithmClientError
from app.models import ChatMessage, LegalCase, ProfileCandidate, User
from app.schemas.chat import ChatStreamRequest

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/stream")
async def stream_chat(
    payload: ChatStreamRequest,
    request: Request,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> StreamingResponse:
    content = payload.message.strip()
    case = _resolve_case(payload.case_id, content, current_user, db)
    trace_id = getattr(request.state, "trace_id", None) or ""

    db.add(
        ChatMessage(
            case_id=case.id,
            user_id=current_user.id,
            role="user",
            content=content,
            trace_id=trace_id,
        )
    )
    db.commit()

    async def event_stream() -> AsyncIterator[str]:
        yield _sse("status", {"stage": "received", "case_id": case.id, "trace_id": trace_id})
        try:
            yield _sse("status", {"stage": "algorithm_analyzing", "case_id": case.id})
            result = await AlgorithmClient().analyze_case(
                {
                    "case_id": case.id,
                    "message": content,
                    "user_id": current_user.id,
                },
                trace_id=trace_id,
            )
        except AlgorithmClientError as exc:
            result = _fallback_result(content, str(exc))
            yield _sse(
                "status",
                {
                    "stage": "algorithm_degraded",
                    "message": "算法端暂不可用，已返回可读降级提示。",
                },
            )

        _persist_analysis_result(
            case_id=case.id,
            user_id=current_user.id,
            trace_id=trace_id,
            content=result.get("answer") or result.get("summary") or "已完成分析。",
            result=result,
        )
        yield _sse("final", result)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def _resolve_case(
    case_id: str | None,
    content: str,
    current_user: User,
    db: Session,
) -> LegalCase:
    if case_id:
        return require_case_for_user(case_id, current_user, db)

    title = content[:32] or "劳动争议咨询"
    case = LegalCase(
        user_id=current_user.id,
        title=title,
        domain="labor_dispute",
        status="open",
        summary=content,
    )
    db.add(case)
    db.flush()
    return case


def _persist_analysis_result(
    case_id: str,
    user_id: str,
    trace_id: str,
    content: str,
    result: dict[str, Any],
) -> None:
    with SessionLocal() as db:
        case = db.get(LegalCase, case_id)
        if case is not None:
            case.summary = result.get("summary") or case.summary
            case.cause = result.get("cause") or case.cause
            case.confidence = result.get("confidence") or case.confidence
            db.add(case)

        db.add(
            ChatMessage(
                case_id=case_id,
                user_id=user_id,
                role="assistant",
                content=content,
                structured_result=result,
                trace_id=trace_id,
            )
        )
        for item in result.get("profile_candidates", []):
            if not isinstance(item, dict):
                continue
            candidate_type = str(item.get("candidate_type") or "fact")
            content_json = item.get("content_json")
            if not isinstance(content_json, dict):
                content_json = {"value": content_json}
            db.add(
                ProfileCandidate(
                    case_id=case_id,
                    candidate_type=candidate_type,
                    content_json=content_json,
                    status=str(item.get("status") or "pending"),
                )
            )
        db.commit()


def _fallback_result(message: str, error_message: str) -> dict[str, Any]:
    return {
        "summary": message,
        "cause": None,
        "confidence": None,
        "issues": [],
        "evidence_gaps": ["算法端暂不可用，建议先补充劳动合同、工资流水、考勤记录等材料。"],
        "strategy": ["稍后重试智能分析，或先整理关键时间、工资标准、合同与解除经过。"],
        "deadline_risk": "暂无法自动判断时效，请先确认争议发生或知道权利受侵害的日期。",
        "answer": "算法端暂不可用，已保存你的问题。请稍后重试，或先补充关键事实和证据材料。",
        "profile_candidates": [],
        "degraded": True,
        "error": error_message,
    }


def _sse(event: str, data: dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False, default=str)}\n\n"
