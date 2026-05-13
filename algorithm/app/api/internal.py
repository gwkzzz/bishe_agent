from fastapi import APIRouter, Depends, Request

from app.core.security import verify_internal_token
from app.graph.labor_consultation import (
    analyze_evidence_mock,
    generate_arbitration_document_mock,
    run_labor_consultation,
)
from app.retrieval.schema_mapping import search_law_basis, search_precedent_references
from app.safety.policy import SafetyPolicyService
from app.schemas.internal import (
    AgentAnalyzeRequest,
    AgentAnalyzeResponse,
    ArbitrationDocumentRequest,
    ArbitrationDocumentResponse,
    CaseSearchResponse,
    EvidenceAnalyzeRequest,
    EvidenceAnalyzeResponse,
    LawSearchResponse,
    RagSearchRequest,
    SafetyReviewRequest,
    SafetyReviewResponse,
)

router = APIRouter(
    prefix="/internal",
    tags=["internal"],
    dependencies=[Depends(verify_internal_token)],
)


@router.get("/ping")
async def internal_ping(request: Request) -> dict[str, str | None]:
    return {
        "status": "ok",
        "service": "algorithm",
        "trace_id": getattr(request.state, "trace_id", None),
    }


@router.post("/agent/analyze", response_model=AgentAnalyzeResponse)
async def analyze_agent(payload: AgentAnalyzeRequest, request: Request) -> AgentAnalyzeResponse:
    return run_labor_consultation(
        payload,
        trace_id=getattr(request.state, "trace_id", None),
    )


@router.post("/evidence/analyze", response_model=EvidenceAnalyzeResponse)
async def analyze_evidence(
    payload: EvidenceAnalyzeRequest,
    request: Request,
) -> EvidenceAnalyzeResponse:
    return analyze_evidence_mock(payload, trace_id=getattr(request.state, "trace_id", None))


@router.post("/documents/arbitration", response_model=ArbitrationDocumentResponse)
async def generate_arbitration_document(
    payload: ArbitrationDocumentRequest,
    request: Request,
) -> ArbitrationDocumentResponse:
    return generate_arbitration_document_mock(
        case_id=payload.case_id,
        summary=payload.summary,
        cause=payload.cause,
        facts=payload.facts,
        evidence=payload.evidence,
        legal_basis=payload.legal_basis,
        trace_id=getattr(request.state, "trace_id", None),
    )


@router.post("/rag/search-laws", response_model=LawSearchResponse)
async def search_laws(payload: RagSearchRequest, request: Request) -> LawSearchResponse:
    trace_id = getattr(request.state, "trace_id", None)
    return LawSearchResponse(
        trace_id=trace_id,
        query=payload.query,
        results=search_law_basis(
            payload.query,
            top_k=payload.top_k,
            trace_id=trace_id,
            case_id=payload.case_id,
        ),
    )


@router.post("/rag/search-cases", response_model=CaseSearchResponse)
async def search_cases(payload: RagSearchRequest, request: Request) -> CaseSearchResponse:
    trace_id = getattr(request.state, "trace_id", None)
    return CaseSearchResponse(
        trace_id=trace_id,
        query=payload.query,
        results=search_precedent_references(
            payload.query,
            top_k=payload.top_k,
            trace_id=trace_id,
            case_id=payload.case_id,
        ),
    )


@router.post("/safety/review", response_model=SafetyReviewResponse)
async def review_safety(
    payload: SafetyReviewRequest,
    request: Request,
) -> SafetyReviewResponse:
    review = SafetyPolicyService().review_text(payload.text)
    citation_warnings: list[str] = []
    if not payload.source_ids and not payload.source_urls:
        citation_warnings.append("未提供可追溯 source_id 或 source_url。")

    return SafetyReviewResponse(
        trace_id=getattr(request.state, "trace_id", None),
        allowed=review.allowed,
        reviewed_text=review.rewritten_text,
        risk_flags=review.risk_flags,
        citation_warnings=citation_warnings,
    )
