from __future__ import annotations

import re
from collections.abc import Callable
from typing import Any, Literal, TypedDict

import structlog
from langgraph.graph import END, START, StateGraph

from app.retrieval.schema_mapping import search_law_basis, search_precedent_references
from app.safety.policy import SafetyPolicyService
from app.schemas.internal import (
    AgentAnalyzeRequest,
    AgentAnalyzeResponse,
    ArbitrationDocumentResponse,
    CauseCandidate,
    DeadlineRisk,
    EvidenceAnalysisResult,
    EvidenceAnalyzeRequest,
    EvidenceAnalyzeResponse,
    EvidenceFinding,
    ExtractedFact,
    IntakeSummary,
    LaborCauseResult,
    LaborRelation,
    LegalBasis,
    PrecedentReference,
    ProfileCandidate,
    StrategyStep,
)


logger = structlog.get_logger(__name__)


class ConsultationState(TypedDict, total=False):
    case_id: str
    user_id: str | None
    message: str
    normalized_message: str
    trace_id: str | None
    need_arbitration_document: bool
    pii_flags: list[str]
    intent: str
    unsafe_allowed: bool
    risk_flags: list[str]
    intake: IntakeSummary
    needs_more_info: bool
    questions: list[str]
    cause_result: LaborCauseResult
    legal_basis: list[LegalBasis]
    precedents: list[PrecedentReference]
    evidence_analysis: EvidenceAnalysisResult
    deadline: DeadlineRisk
    profile_candidates: list[ProfileCandidate]
    issues: list[dict[str, Any]]
    strategy_steps: list[StrategyStep]
    strategy: list[str]
    arbitration_document: ArbitrationDocumentResponse | None
    answer: str
    safety_notice: str
    final_response: AgentAnalyzeResponse
    node_trace: list[str]


NodeFn = Callable[[ConsultationState], dict[str, Any]]


def run_labor_consultation(
    payload: AgentAnalyzeRequest,
    trace_id: str | None = None,
) -> AgentAnalyzeResponse:
    graph = _compiled_graph()
    final_state = graph.invoke(
        {
            "case_id": payload.case_id,
            "user_id": payload.user_id,
            "message": payload.message,
            "trace_id": trace_id,
            "need_arbitration_document": payload.need_arbitration_document,
            "node_trace": [],
        }
    )
    return final_state["final_response"]


def analyze_evidence_mock(
    payload: EvidenceAnalyzeRequest,
    trace_id: str | None = None,
) -> EvidenceAnalyzeResponse:
    text = (payload.text or "").strip() or None
    name = payload.name or _evidence_name_from_payload(payload)
    finding = EvidenceFinding(
        name=name,
        evidence_type=payload.evidence_type or _guess_evidence_type(name, text),
        proves=_guess_evidence_proves(name, text),
        strength=_guess_evidence_strength(name, text),
        risk=_guess_evidence_risk(name, text),
    )
    missing = _missing_evidence_for_text(text or name)
    analysis = EvidenceAnalysisResult(evidence_items=[finding], missing_evidence=missing)
    return EvidenceAnalyzeResponse(
        trace_id=trace_id,
        evidence_id=payload.evidence_id,
        case_id=payload.case_id,
        status="mocked",
        extracted_text=text,
        analysis=analysis,
        proves=finding.proves,
        strength=finding.strength,
        risk=finding.risk,
        missing_evidence=missing,
    )


def search_mock_laws(query: str, top_k: int = 5) -> list[LegalBasis]:
    return search_law_basis(query, top_k=top_k)


def search_mock_precedents(query: str, top_k: int = 5) -> list[PrecedentReference]:
    return search_precedent_references(query, top_k=top_k)


def generate_arbitration_document_mock(
    case_id: str,
    summary: str | None,
    cause: str | None,
    facts: list[str],
    evidence: list[str],
    legal_basis: list[LegalBasis] | None = None,
    trace_id: str | None = None,
) -> ArbitrationDocumentResponse:
    missing_fields = []
    if not summary:
        missing_fields.append("案情摘要")
    if not facts:
        missing_fields.append("主要事实")
    if not evidence:
        missing_fields.append("证据目录")

    law_lines = [
        f"- {item.title}{item.article or ''}：{item.summary}"
        for item in legal_basis or []
        if item.source_id or item.source_url
    ]
    content = "\n".join(
        [
            "# 劳动仲裁申请书",
            "",
            "## 申请人",
            "待补充姓名、身份证号、联系方式、住址",
            "",
            "## 被申请人",
            "待补充用人单位名称、统一社会信用代码、住所地、法定代表人",
            "",
            "## 仲裁请求",
            _document_claim_for_cause(cause),
            "",
            "## 事实与理由",
            summary or "待补充案情摘要",
            "",
            "### 主要事实",
            *[f"- {item}" for item in (facts or ["待补充入职时间、岗位、工资标准、争议经过"])],
            "",
            "## 证据目录",
            *[f"- {item}" for item in (evidence or ["待补充劳动合同、工资流水、考勤记录、沟通记录"])],
            "",
            "## 法律依据",
            *(law_lines or ["- 待结合检索结果补充，不应虚构法条。"]),
            "",
            "## 风险提示",
            "本初稿仅供参考，提交前需要由专业人士复核。",
        ]
    )
    return ArbitrationDocumentResponse(
        trace_id=trace_id,
        case_id=case_id,
        content_md=content,
        status="draft",
        missing_fields=missing_fields,
    )


def _compiled_graph():
    if not hasattr(_compiled_graph, "graph"):
        workflow = StateGraph(ConsultationState)
        workflow.add_node("input_normalize", _logged_node("input_normalize", _input_normalize))
        workflow.add_node("pii_detect", _logged_node("pii_detect", _pii_detect))
        workflow.add_node("intent_detect", _logged_node("intent_detect", _intent_detect))
        workflow.add_node(
            "unsafe_request_detect",
            _logged_node("unsafe_request_detect", _unsafe_request_detect),
        )
        workflow.add_node("intake_extract", _logged_node("intake_extract", _intake_extract))
        workflow.add_node("need_more_info", _logged_node("need_more_info", _need_more_info))
        workflow.add_node(
            "labor_cause_classify",
            _logged_node("labor_cause_classify", _labor_cause_classify),
        )
        workflow.add_node(
            "parallel_analysis",
            _logged_node("parallel_analysis", _parallel_analysis),
        )
        workflow.add_node(
            "retrieval_merge_and_rerank",
            _logged_node("retrieval_merge_and_rerank", _retrieval_merge_and_rerank),
        )
        workflow.add_node("issue_analyze", _logged_node("issue_analyze", _issue_analyze))
        workflow.add_node("strategy_plan", _logged_node("strategy_plan", _strategy_plan))
        workflow.add_node(
            "arbitration_document_generate",
            _logged_node("arbitration_document_generate", _arbitration_document_generate),
        )
        workflow.add_node("answer_compose", _logged_node("answer_compose", _answer_compose))
        workflow.add_node("safety_review", _logged_node("safety_review", _safety_review))
        workflow.add_node("final_response", _logged_node("final_response", _final_response))

        workflow.add_edge(START, "input_normalize")
        workflow.add_edge("input_normalize", "pii_detect")
        workflow.add_edge("pii_detect", "intent_detect")
        workflow.add_edge("intent_detect", "unsafe_request_detect")
        workflow.add_edge("unsafe_request_detect", "intake_extract")
        workflow.add_edge("intake_extract", "need_more_info")
        workflow.add_conditional_edges(
            "need_more_info",
            _route_after_need_more_info,
            {
                "ask_user": "answer_compose",
                "continue": "labor_cause_classify",
            },
        )
        workflow.add_edge("labor_cause_classify", "parallel_analysis")
        workflow.add_edge("parallel_analysis", "retrieval_merge_and_rerank")
        workflow.add_edge("retrieval_merge_and_rerank", "issue_analyze")
        workflow.add_edge("issue_analyze", "strategy_plan")
        workflow.add_edge("strategy_plan", "arbitration_document_generate")
        workflow.add_edge("arbitration_document_generate", "answer_compose")
        workflow.add_edge("answer_compose", "safety_review")
        workflow.add_edge("safety_review", "final_response")
        workflow.add_edge("final_response", END)
        _compiled_graph.graph = workflow.compile()
    return _compiled_graph.graph


def _logged_node(name: str, node_fn: NodeFn) -> NodeFn:
    def wrapped(state: ConsultationState) -> dict[str, Any]:
        trace_id = state.get("trace_id")
        logger.info("agent_node_start", node=name, trace_id=trace_id, case_id=state.get("case_id"))
        try:
            update = node_fn(state)
            trace = [*state.get("node_trace", []), name]
            update["node_trace"] = trace
            logger.info(
                "agent_node_complete",
                node=name,
                trace_id=trace_id,
                case_id=state.get("case_id"),
            )
            return update
        except Exception as exc:
            logger.exception(
                "agent_node_failed",
                node=name,
                trace_id=trace_id,
                case_id=state.get("case_id"),
                error=str(exc),
            )
            raise

    return wrapped


def _input_normalize(state: ConsultationState) -> dict[str, Any]:
    normalized = re.sub(r"\s+", " ", state["message"]).strip()
    return {"normalized_message": normalized}


def _pii_detect(state: ConsultationState) -> dict[str, Any]:
    message = state["normalized_message"]
    flags: list[str] = []
    if re.search(r"1[3-9]\d{9}", message):
        flags.append("phone_number")
    if re.search(r"\d{17}[\dXx]", message):
        flags.append("id_card_number")
    return {"pii_flags": flags}


def _intent_detect(state: ConsultationState) -> dict[str, Any]:
    message = state["normalized_message"]
    if any(keyword in message for keyword in _LABOR_KEYWORDS):
        intent = "labor_consultation"
    elif any(keyword in message for keyword in ("离婚", "借款", "交通事故", "刑事")):
        intent = "unsupported_legal_domain"
    else:
        intent = "unclear"
    return {"intent": intent}


def _unsafe_request_detect(state: ConsultationState) -> dict[str, Any]:
    review = SafetyPolicyService().review_text(state["normalized_message"])
    return {
        "unsafe_allowed": review.allowed,
        "risk_flags": review.risk_flags,
    }


def _intake_extract(state: ConsultationState) -> dict[str, Any]:
    message = state["normalized_message"]
    facts = [ExtractedFact(fact=_fact_sentence(message), confidence=0.82)]
    missing_questions = _missing_questions(message)
    intake = IntakeSummary(
        summary=f"用户描述：{message}",
        labor_relation=LaborRelation(
            employer=_extract_employer_hint(message),
            employee="用户",
            start_date=_extract_date_hint(message, ("入职", "上班")),
            end_date=_extract_date_hint(message, ("离职", "辞退", "解除")),
            salary=_extract_salary_hint(message),
            has_written_contract=_extract_contract_hint(message),
        ),
        facts=facts,
        claims=_claims_for_message(message),
        missing_questions=missing_questions,
    )
    return {"intake": intake}


def _need_more_info(state: ConsultationState) -> dict[str, Any]:
    if state.get("unsafe_allowed") is False:
        return {"needs_more_info": True, "questions": []}

    message = state["normalized_message"]
    intake = state["intake"]
    if state.get("intent") != "labor_consultation":
        return {
            "needs_more_info": True,
            "questions": ["请补充这是劳动用工、工资、合同、解除、加班或离职证明中的哪类争议？"],
        }

    enough = _has_time_hint(message) or _has_evidence_hint(message) or len(message) >= 20
    if not enough:
        return {"needs_more_info": True, "questions": intake.missing_questions[:4]}

    return {"needs_more_info": False, "questions": []}


def _labor_cause_classify(state: ConsultationState) -> dict[str, Any]:
    candidates = _cause_candidates(state["normalized_message"])
    cause_result = LaborCauseResult(
        possible_causes=candidates,
        risk_flags=["需关注劳动仲裁时效"],
    )
    return {"cause_result": cause_result}


def _parallel_analysis(state: ConsultationState) -> dict[str, Any]:
    query = state["normalized_message"]
    legal_basis = search_mock_laws(query, top_k=3)
    precedents = search_mock_precedents(query, top_k=2)
    evidence_analysis = EvidenceAnalysisResult(
        evidence_items=_evidence_findings_from_message(query),
        missing_evidence=_missing_evidence_for_text(query),
    )
    deadline = _deadline_from_message(query)
    profile_candidates = _profile_candidates_from_state(state, evidence_analysis)
    return {
        "legal_basis": legal_basis,
        "precedents": precedents,
        "evidence_analysis": evidence_analysis,
        "deadline": deadline,
        "profile_candidates": profile_candidates,
    }


def _retrieval_merge_and_rerank(state: ConsultationState) -> dict[str, Any]:
    legal_basis = [
        item.model_copy(update={"verified": bool(item.source_id or item.source_url)})
        for item in state.get("legal_basis", [])
    ]
    precedents = [
        item.model_copy(update={"verified": bool(item.source_id or item.source_url)})
        for item in state.get("precedents", [])
    ]
    legal_basis.sort(key=lambda item: item.score, reverse=True)
    precedents.sort(key=lambda item: item.score, reverse=True)
    return {"legal_basis": legal_basis, "precedents": precedents}


def _issue_analyze(state: ConsultationState) -> dict[str, Any]:
    message = state["normalized_message"]
    gaps = state["evidence_analysis"].missing_evidence
    issues = [
        {
            "issue": "双方是否存在劳动关系",
            "burden_of_proof": "用户需初步证明接受用人单位管理并持续提供劳动。",
            "current_evidence_status": _status_from_gap("劳动合同", gaps),
            "needed_evidence": ["劳动合同", "工资流水", "考勤记录", "工牌或工作沟通记录"],
            "impact": "high",
        },
        {
            "issue": _main_issue_for_message(message),
            "burden_of_proof": "用户需说明请求事项、期间、金额或解除经过，并用证据相互印证。",
            "current_evidence_status": "待补充" if gaps else "已有初步线索",
            "needed_evidence": gaps or ["证据原件", "完整沟通上下文"],
            "impact": "high" if gaps else "medium",
        },
    ]
    return {"issues": issues}


def _strategy_plan(state: ConsultationState) -> dict[str, Any]:
    gaps = state["evidence_analysis"].missing_evidence
    deadline = state["deadline"]
    steps = [
        StrategyStep(
            step="协商与固定事实",
            action="先整理入职时间、岗位、工资标准、争议发生时间和沟通过程，并保留原始证据。",
            materials=["劳动合同或入职材料", "工资流水", "考勤记录", "聊天记录"],
            risk_hint="不要补做或伪造证据，尽量保留原始载体。",
        ),
        StrategyStep(
            step="投诉或调解",
            action="可视情况向劳动监察、调解组织反映，保留提交材料和处理回执。",
            materials=gaps or ["证据目录", "事实时间线"],
            risk_hint="调解不影响继续准备仲裁材料。",
        ),
        StrategyStep(
            step="劳动仲裁",
            action="协商无果时，围绕明确请求、事实理由和证据目录准备劳动仲裁申请。",
            materials=["仲裁申请书", "身份证明", "用人单位主体信息", "证据目录"],
            risk_hint=deadline.message,
        ),
    ]
    return {"strategy_steps": steps, "strategy": [step.action for step in steps]}


def _arbitration_document_generate(state: ConsultationState) -> dict[str, Any]:
    if not state.get("need_arbitration_document", True):
        return {"arbitration_document": None}

    intake = state["intake"]
    cause = _primary_cause(state)
    document = generate_arbitration_document_mock(
        case_id=state["case_id"],
        summary=intake.summary,
        cause=cause,
        facts=[fact.fact for fact in intake.facts],
        evidence=[item.name for item in state["evidence_analysis"].evidence_items],
        legal_basis=state.get("legal_basis", []),
        trace_id=state.get("trace_id"),
    )
    return {"arbitration_document": document}


def _answer_compose(state: ConsultationState) -> dict[str, Any]:
    if state.get("unsafe_allowed") is False:
        answer = (
            "我不能帮助伪造证据、补做虚假材料、威胁对方或规避法律程序。"
            "如果你需要维护权益，可以补充真实争议经过和现有证据，我可以帮你整理合法的处理路径。"
        )
        return {"answer": answer}

    if state.get("needs_more_info"):
        questions = state.get("questions") or state["intake"].missing_questions[:4]
        answer = "\n".join(
            [
                "根据你目前提供的信息，还缺少关键事实，暂不继续生成结论。",
                "请先补充：",
                *[f"- {question}" for question in questions],
            ]
        )
        return {"answer": answer}

    intake = state["intake"]
    cause = _primary_cause(state)
    legal_basis = state.get("legal_basis", [])
    precedents = state.get("precedents", [])
    issues = state.get("issues", [])
    evidence_analysis = state["evidence_analysis"]
    deadline = state["deadline"]
    profile_candidates = state.get("profile_candidates", [])
    answer = "\n".join(
        [
            f"案情摘要：{intake.summary}",
            f"劳动争议子类型：根据现有描述，可能涉及{cause}。",
            "关键争议焦点："
            + "；".join(str(issue["issue"]) for issue in issues),
            "现有证据分析："
            + (
                "；".join(
                    f"{item.name}可用于证明{item.proves}，证明力暂评为{item.strength}"
                    for item in evidence_analysis.evidence_items
                )
                or "尚未提供可分析证据"
            ),
            "需要补充的信息或证据：" + "、".join(evidence_analysis.missing_evidence),
            "相关法律依据："
            + "；".join(f"{item.title}{item.article or ''}" for item in legal_basis),
            "类案参考："
            + ("；".join(item.title for item in precedents) if precedents else "暂无可引用类案"),
            "处理路径：" + "；".join(state.get("strategy", [])),
            f"时效风险：{deadline.message}",
            f"档案更新候选项：已生成 {len(profile_candidates)} 条待确认候选项。",
            "以上判断仍需结合劳动合同、工资流水、考勤记录、沟通记录等证据进一步判断。",
        ]
    )
    return {"answer": answer}


def _safety_review(state: ConsultationState) -> dict[str, Any]:
    review = SafetyPolicyService().review_text(state["answer"])
    citation_warnings = [
        item.title
        for item in [*state.get("legal_basis", []), *state.get("precedents", [])]
        if not (item.source_id or item.source_url)
    ]
    risk_flags = [*state.get("risk_flags", []), *review.risk_flags]
    if citation_warnings:
        risk_flags.append("citation_missing_source")
    return {
        "answer": review.rewritten_text,
        "risk_flags": risk_flags,
        "safety_notice": "以上内容仅供参考，不能替代专业法律意见。",
    }


def _final_response(state: ConsultationState) -> dict[str, Any]:
    intake = state.get("intake")
    cause = _primary_cause(state) if state.get("cause_result") else None
    confidence = (
        state["cause_result"].possible_causes[0].confidence
        if state.get("cause_result") and state["cause_result"].possible_causes
        else None
    )
    evidence_analysis = state.get("evidence_analysis") or EvidenceAnalysisResult()
    deadline = state.get("deadline")
    response = AgentAnalyzeResponse(
        trace_id=state.get("trace_id"),
        case_id=state["case_id"],
        summary=intake.summary if intake else state.get("normalized_message", ""),
        cause=cause,
        confidence=confidence,
        needs_more_info=state.get("needs_more_info", False),
        questions=state.get("questions", []),
        intake=intake,
        cause_result=state.get("cause_result"),
        issues=state.get("issues", []),
        evidence_analysis=evidence_analysis,
        evidence_gaps=evidence_analysis.missing_evidence,
        strategy_steps=state.get("strategy_steps", []),
        strategy=state.get("strategy", []),
        deadline=deadline,
        deadline_risk=deadline.message if deadline else None,
        legal_basis=state.get("legal_basis", []),
        precedents=state.get("precedents", []),
        profile_candidates=state.get("profile_candidates", []),
        arbitration_document=state.get("arbitration_document"),
        answer=state["answer"],
        safety_notice=state.get("safety_notice", "以上内容仅供参考，不能替代专业法律意见。"),
        risk_flags=state.get("risk_flags", []),
        node_trace=[*state.get("node_trace", []), "final_response"],
    )
    return {"final_response": response}


def _route_after_need_more_info(state: ConsultationState) -> Literal["ask_user", "continue"]:
    if state.get("needs_more_info"):
        return "ask_user"
    return "continue"


def _rank_by_query(
    query: str,
    candidates: list[Any],
    key: Callable[[Any], str],
) -> list[Any]:
    scored = []
    for candidate in candidates:
        text = key(candidate)
        overlap = sum(1 for token in _query_tokens(query) if token in text)
        scored.append((overlap, candidate.score, candidate))
    scored.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return [item[2] for item in scored]


def _query_tokens(query: str) -> list[str]:
    return [
        token
        for token in ("工资", "拖欠", "合同", "未签", "辞退", "解除", "加班", "离职证明", "时效")
        if token in query
    ]


def _cause_candidates(message: str) -> list[CauseCandidate]:
    candidates: list[CauseCandidate] = []
    if "工资" in message or "拖欠" in message or "报酬" in message:
        candidates.append(CauseCandidate(cause="追索劳动报酬", confidence=0.88))
    if "未签" in message or "合同" in message:
        candidates.append(CauseCandidate(cause="劳动合同纠纷", confidence=0.82))
    if "辞退" in message or "解除" in message or "赔偿" in message:
        candidates.append(CauseCandidate(cause="违法解除争议", confidence=0.8))
    if "加班" in message:
        candidates.append(CauseCandidate(cause="加班费争议", confidence=0.78))
    if "离职证明" in message:
        candidates.append(CauseCandidate(cause="离职证明争议", confidence=0.76))
    return candidates or [CauseCandidate(cause="劳动争议", confidence=0.65)]


def _primary_cause(state: ConsultationState) -> str:
    cause_result = state.get("cause_result")
    if cause_result and cause_result.possible_causes:
        return cause_result.possible_causes[0].cause
    return "劳动争议"


def _claims_for_message(message: str) -> list[str]:
    claims: list[str] = []
    if "工资" in message or "拖欠" in message:
        claims.append("支付拖欠工资")
    if "未签" in message or "合同" in message:
        claims.append("确认劳动关系或主张未签书面劳动合同责任")
    if "辞退" in message or "解除" in message or "赔偿" in message:
        claims.append("确认解除合法性并评估赔偿或补偿")
    if "加班" in message:
        claims.append("支付加班费")
    if "离职证明" in message:
        claims.append("开具离职证明")
    return claims or ["待结合事实明确仲裁请求"]


def _fact_sentence(message: str) -> str:
    if len(message) <= 80:
        return message
    return f"{message[:77]}..."


def _extract_employer_hint(message: str) -> str | None:
    if "公司" in message:
        return "用人单位"
    return None


def _extract_date_hint(message: str, anchors: tuple[str, ...]) -> str | None:
    for anchor in anchors:
        match = re.search(rf"(\d{{4}}年\d{{1,2}}月|\d{{1,2}}月|\d+天前|\d+个月前).{{0,8}}{anchor}", message)
        if match:
            return match.group(1)
        match = re.search(rf"{anchor}.{{0,8}}(\d{{4}}年\d{{1,2}}月|\d{{1,2}}月|\d+天前|\d+个月前)", message)
        if match:
            return match.group(1)
    return None


def _extract_salary_hint(message: str) -> str | None:
    match = re.search(r"(月薪|工资|薪资).{0,6}?(\d+(?:\.\d+)?[万千元块]?)", message)
    if match:
        return match.group(2)
    return None


def _extract_contract_hint(message: str) -> bool | None:
    if "未签" in message or "没签" in message or "没有签" in message:
        return False
    if "签了合同" in message or "有合同" in message:
        return True
    return None


def _missing_questions(message: str) -> list[str]:
    questions = []
    if not _has_time_hint(message):
        questions.append("入职时间、离职或解除时间、争议发生时间分别是什么？")
    if not _extract_salary_hint(message) and ("工资" in message or "加班" in message):
        questions.append("工资标准、欠付期间、欠付金额或加班计算方式是什么？")
    if _extract_contract_hint(message) is None:
        questions.append("是否签订书面劳动合同，是否有社保、工牌、考勤或工资流水？")
    if not _has_evidence_hint(message):
        questions.append("目前有哪些证据，能否保留原始载体和完整上下文？")
    return questions


def _has_time_hint(message: str) -> bool:
    return bool(
        re.search(r"\d{4}年|\d{1,2}月|\d+天前|\d+个月|一年|两年|三年|昨天|今天|去年|上个月", message)
    )


def _has_evidence_hint(message: str) -> bool:
    return any(keyword in message for keyword in ("合同", "流水", "考勤", "聊天", "微信", "通知", "录音", "证据"))


def _evidence_findings_from_message(message: str) -> list[EvidenceFinding]:
    findings: list[EvidenceFinding] = []
    if "合同" in message:
        findings.append(
            EvidenceFinding(
                name="劳动合同或入职材料",
                evidence_type="书证",
                proves="劳动关系、岗位、工资标准和合同期限",
                strength="high",
                risk="需核对签署主体、日期和完整文本。",
            )
        )
    if "流水" in message or "工资" in message:
        findings.append(
            EvidenceFinding(
                name="工资流水或支付记录",
                evidence_type="电子数据/书证",
                proves="工资标准、支付周期和欠付金额",
                strength="medium",
                risk="需与考勤、合同或聊天记录相互印证。",
            )
        )
    if "聊天" in message or "微信" in message:
        findings.append(
            EvidenceFinding(
                name="沟通记录",
                evidence_type="电子数据",
                proves="双方对工资、解除或离职证明问题的沟通过程",
                strength="medium",
                risk="截图证明力有限，建议保留原始载体和完整上下文。",
            )
        )
    return findings


def _evidence_name_from_payload(payload: EvidenceAnalyzeRequest) -> str:
    if payload.file_url:
        return payload.file_url.rsplit("/", 1)[-1] or "待分析证据"
    return "待分析证据"


def _guess_evidence_type(name: str, text: str | None) -> str:
    content = f"{name} {text or ''}"
    if any(keyword in content for keyword in ("微信", "聊天", "截图", "短信")):
        return "电子数据"
    if any(keyword in content for keyword in ("合同", "通知", "证明")):
        return "书证"
    if any(keyword in content for keyword in ("流水", "转账", "银行")):
        return "书证/电子数据"
    return "待分类"


def _guess_evidence_proves(name: str, text: str | None) -> str:
    content = f"{name} {text or ''}"
    if "工资" in content or "流水" in content or "转账" in content:
        return "工资标准、支付记录或欠付情况"
    if "合同" in content:
        return "劳动关系、岗位、工资标准和合同期限"
    if "辞退" in content or "解除" in content or "通知" in content:
        return "解除经过、解除时间和用人单位意思表示"
    if "聊天" in content or "微信" in content:
        return "双方就争议事项的沟通过程"
    return "待结合案情确认该证据的证明对象"


def _guess_evidence_strength(name: str, text: str | None) -> Literal["unknown", "low", "medium", "high"]:
    content = f"{name} {text or ''}"
    if "合同" in content or "银行" in content or "流水" in content:
        return "high"
    if "聊天" in content or "微信" in content or "通知" in content:
        return "medium"
    return "unknown"


def _guess_evidence_risk(name: str, text: str | None) -> str:
    content = f"{name} {text or ''}"
    if "截图" in content or "聊天" in content or "微信" in content:
        return "仅有截图时证明力可能受限，建议保留原始设备、完整上下文和导出记录。"
    if "复印" in content:
        return "复印件需尽量补充原件或能证明真实性的辅助材料。"
    return "当前为 mock 分析结果，后续需接入 OCR/文档解析并复核真实性。"


def _missing_evidence_for_text(text: str) -> list[str]:
    missing = []
    if "合同" not in text:
        missing.append("劳动合同或能证明劳动关系的材料")
    if "流水" not in text and "工资" in text:
        missing.append("银行工资流水或工资条")
    if "考勤" not in text:
        missing.append("考勤记录或排班记录")
    if "聊天" not in text and "微信" not in text:
        missing.append("与用人单位的完整沟通记录")
    return missing or ["证据原始载体和完整上下文"]


def _deadline_from_message(message: str) -> DeadlineRisk:
    if not _has_time_hint(message):
        return DeadlineRisk(
            risk_level="unknown",
            message="缺少争议发生或知道权利受侵害的日期，需补充后判断劳动仲裁时效。",
        )
    if "两年" in message or "三年" in message or "去年" in message:
        return DeadlineRisk(
            risk_level="medium",
            message="已出现较早时间线，需核对是否超过一年劳动仲裁时效及是否存在中断、中止事实。",
        )
    return DeadlineRisk(
        risk_level="low",
        message="目前未发现明显临近时效风险，但仍需结合具体日期复核一年仲裁时效。",
    )


def _profile_candidates_from_state(
    state: ConsultationState,
    evidence_analysis: EvidenceAnalysisResult,
) -> list[ProfileCandidate]:
    intake = state["intake"]
    candidates = [
        ProfileCandidate(
            candidate_type="fact",
            content_json={
                "fact_text": intake.summary,
                "source": "user_message",
                "confidence": 0.82,
            },
        ),
        ProfileCandidate(
            candidate_type="todo",
            content_json={
                "title": "补充关键事实和证据",
                "items": intake.missing_questions or evidence_analysis.missing_evidence,
            },
        ),
    ]
    for item in evidence_analysis.evidence_items:
        candidates.append(
            ProfileCandidate(
                candidate_type="evidence",
                content_json={
                    "name": item.name,
                    "proves": item.proves,
                    "strength": item.strength,
                    "risk": item.risk,
                },
            )
        )
    return candidates


def _status_from_gap(keyword: str, gaps: list[str]) -> str:
    return "证据不足" if any(keyword in gap for gap in gaps) else "已有初步线索"


def _main_issue_for_message(message: str) -> str:
    if "工资" in message or "拖欠" in message:
        return "用人单位是否欠付工资及金额如何计算"
    if "未签" in message or "合同" in message:
        return "未签书面劳动合同责任及期间如何认定"
    if "辞退" in message or "解除" in message:
        return "解除是否合法以及补偿或赔偿如何主张"
    if "加班" in message:
        return "加班事实、审批安排和加班费金额如何证明"
    if "离职证明" in message:
        return "用人单位是否负有开具离职证明义务"
    return "请求事项和事实依据是否明确"


def _document_claim_for_cause(cause: str | None) -> str:
    if cause == "追索劳动报酬":
        return "请求裁决被申请人支付拖欠工资，具体金额和计算方式待补充。"
    if cause == "劳动合同纠纷":
        return "请求确认劳动关系或承担未签书面劳动合同相关责任，具体期间待补充。"
    if cause == "违法解除争议":
        return "请求确认解除行为违法并承担相应责任，具体请求待补充。"
    if cause == "加班费争议":
        return "请求裁决被申请人支付加班费，具体期间、时长和计算方式待补充。"
    if cause == "离职证明争议":
        return "请求裁决被申请人依法出具离职证明。"
    return "待补充具体请求、金额和计算方式。"


_LABOR_KEYWORDS = (
    "工资",
    "拖欠",
    "合同",
    "未签",
    "辞退",
    "解除",
    "赔偿",
    "加班",
    "离职证明",
    "社保",
    "劳动",
    "公司",
)
