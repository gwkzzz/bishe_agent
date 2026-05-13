from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class TraceResponse(BaseModel):
    trace_id: str | None = None


class LaborRelation(BaseModel):
    employer: str | None = None
    employee: str | None = "用户"
    start_date: str | None = None
    end_date: str | None = None
    salary: str | None = None
    has_written_contract: bool | None = None


class ExtractedFact(BaseModel):
    fact: str
    time: str | None = None
    source: str = "user_message"
    confidence: float = 0.75


class IntakeSummary(BaseModel):
    summary: str
    labor_relation: LaborRelation = Field(default_factory=LaborRelation)
    facts: list[ExtractedFact] = Field(default_factory=list)
    claims: list[str] = Field(default_factory=list)
    missing_questions: list[str] = Field(default_factory=list)


class CauseCandidate(BaseModel):
    cause: str
    confidence: float = 0.7


class LaborCauseResult(BaseModel):
    primary_domain: str = "劳动争议"
    supported: bool = True
    possible_causes: list[CauseCandidate] = Field(default_factory=list)
    procedure_hint: str = "劳动争议通常需先申请劳动仲裁。"
    risk_flags: list[str] = Field(default_factory=list)


class IssueAnalysis(BaseModel):
    issue: str
    burden_of_proof: str
    current_evidence_status: str
    needed_evidence: list[str] = Field(default_factory=list)
    impact: Literal["low", "medium", "high"] = "medium"


class EvidenceFinding(BaseModel):
    name: str
    evidence_type: str | None = None
    proves: str
    strength: Literal["unknown", "low", "medium", "high"] = "unknown"
    risk: str


class EvidenceAnalysisResult(BaseModel):
    evidence_items: list[EvidenceFinding] = Field(default_factory=list)
    missing_evidence: list[str] = Field(default_factory=list)


class LegalBasis(BaseModel):
    source_id: str
    title: str
    article: str | None = None
    summary: str
    source_url: str | None = None
    score: float = 0.75
    verified: bool = False
    metadata: dict[str, object] = Field(default_factory=dict)


class PrecedentReference(BaseModel):
    source_id: str
    title: str
    cause: str | None = None
    court: str | None = None
    summary: str
    similarities: list[str] = Field(default_factory=list)
    differences: list[str] = Field(default_factory=list)
    source_url: str | None = None
    score: float = 0.65
    verified: bool = False
    metadata: dict[str, object] = Field(default_factory=dict)


class StrategyStep(BaseModel):
    step: str
    action: str
    materials: list[str] = Field(default_factory=list)
    risk_hint: str | None = None


class DeadlineRisk(BaseModel):
    name: str = "劳动仲裁时效"
    due_date: str | None = None
    risk_level: Literal["unknown", "low", "medium", "high"] = "unknown"
    message: str


class ProfileCandidate(BaseModel):
    candidate_type: Literal["timeline", "evidence", "todo", "fact"]
    content_json: dict[str, object]
    status: Literal["pending", "confirmed", "rejected"] = "pending"
    confidence: float = 0.72


class SafetyReviewRequest(BaseModel):
    text: str = Field(min_length=1)
    source_ids: list[str] = Field(default_factory=list)
    source_urls: list[str] = Field(default_factory=list)


class SafetyReviewResponse(TraceResponse):
    allowed: bool
    reviewed_text: str
    risk_flags: list[str] = Field(default_factory=list)
    citation_warnings: list[str] = Field(default_factory=list)
    safety_notice: str = "以上内容仅供参考，不能替代专业法律意见。"


class AgentAnalyzeRequest(BaseModel):
    case_id: str
    message: str = Field(min_length=1)
    user_id: str | None = None
    need_arbitration_document: bool = True


class AgentAnalyzeResponse(TraceResponse):
    case_id: str
    summary: str
    cause: str | None = None
    confidence: float | None = None
    needs_more_info: bool = False
    questions: list[str] = Field(default_factory=list)
    intake: IntakeSummary | None = None
    cause_result: LaborCauseResult | None = None
    issues: list[IssueAnalysis] = Field(default_factory=list)
    evidence_analysis: EvidenceAnalysisResult = Field(default_factory=EvidenceAnalysisResult)
    evidence_gaps: list[str] = Field(default_factory=list)
    strategy_steps: list[StrategyStep] = Field(default_factory=list)
    strategy: list[str] = Field(default_factory=list)
    deadline: DeadlineRisk | None = None
    deadline_risk: str | None = None
    legal_basis: list[LegalBasis] = Field(default_factory=list)
    precedents: list[PrecedentReference] = Field(default_factory=list)
    profile_candidates: list[ProfileCandidate] = Field(default_factory=list)
    arbitration_document: "ArbitrationDocumentResponse | None" = None
    answer: str
    safety_notice: str = "以上内容仅供参考，不能替代专业法律意见。"
    risk_flags: list[str] = Field(default_factory=list)
    node_trace: list[str] = Field(default_factory=list)


class EvidenceAnalyzeRequest(BaseModel):
    evidence_id: str
    case_id: str | None = None
    file_url: str | None = None
    text: str | None = None
    name: str | None = None
    evidence_type: str | None = None


class EvidenceAnalyzeResponse(TraceResponse):
    evidence_id: str
    case_id: str | None = None
    status: Literal["mocked", "parsed", "failed"] = "mocked"
    extracted_text: str | None = None
    analysis: EvidenceAnalysisResult
    proves: str
    strength: Literal["unknown", "low", "medium", "high"] = "unknown"
    risk: str
    missing_evidence: list[str] = Field(default_factory=list)


class ArbitrationDocumentRequest(BaseModel):
    case_id: str
    summary: str | None = None
    cause: str | None = None
    facts: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    legal_basis: list[LegalBasis] = Field(default_factory=list)


class ArbitrationDocumentResponse(TraceResponse):
    case_id: str
    title: str = "劳动仲裁申请书初稿"
    content_md: str
    status: Literal["draft", "confirmed"] = "draft"
    missing_fields: list[str] = Field(default_factory=list)
    safety_notice: str = "以下为仲裁申请书初稿，提交前需要由专业人士复核。"


class RagSearchRequest(BaseModel):
    query: str = Field(min_length=1)
    case_id: str | None = None
    top_k: int = Field(default=5, ge=1, le=20)


class LawSearchResponse(TraceResponse):
    query: str
    results: list[LegalBasis] = Field(default_factory=list)


class CaseSearchResponse(TraceResponse):
    query: str
    results: list[PrecedentReference] = Field(default_factory=list)


AgentAnalyzeResponse.model_rebuild()
