from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app


def _headers(trace_id: str = "test-trace-m3") -> dict[str, str]:
    settings = get_settings()
    return {
        "X-Internal-Token": settings.algorithm_internal_token,
        settings.trace_header_name: trace_id,
    }


def test_agent_analyze_runs_mock_dag() -> None:
    response = TestClient(app).post(
        "/internal/agent/analyze",
        json={
            "case_id": "case-1",
            "user_id": "user-1",
            "message": "公司拖欠我两个月工资，我有工资流水和微信聊天记录。",
        },
        headers=_headers(),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["trace_id"] == "test-trace-m3"
    assert data["case_id"] == "case-1"
    assert data["cause"] == "追索劳动报酬"
    assert data["needs_more_info"] is False
    assert data["issues"]
    assert data["legal_basis"]
    assert data["precedents"]
    assert data["profile_candidates"]
    assert data["arbitration_document"]["content_md"].startswith("# 劳动仲裁申请书")
    assert "input_normalize" in data["node_trace"]
    assert "final_response" in data["node_trace"]


def test_agent_analyze_asks_when_key_facts_missing() -> None:
    response = TestClient(app).post(
        "/internal/agent/analyze",
        json={"case_id": "case-2", "message": "公司欠薪怎么办"},
        headers=_headers(),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["needs_more_info"] is True
    assert data["cause"] is None
    assert data["legal_basis"] == []
    assert data["questions"]
    assert "暂不继续生成结论" in data["answer"]
    assert "labor_cause_classify" not in data["node_trace"]


def test_m3_internal_endpoints_return_stable_contracts() -> None:
    client = TestClient(app)

    evidence = client.post(
        "/internal/evidence/analyze",
        json={
            "evidence_id": "ev-1",
            "case_id": "case-1",
            "name": "工资流水.pdf",
            "text": "银行工资流水显示公司连续两个月未足额支付工资",
        },
        headers=_headers(),
    )
    assert evidence.status_code == 200
    assert evidence.json()["analysis"]["evidence_items"][0]["strength"] == "high"

    document = client.post(
        "/internal/documents/arbitration",
        json={
            "case_id": "case-1",
            "summary": "用户称公司拖欠两个月工资。",
            "cause": "追索劳动报酬",
            "facts": ["公司拖欠两个月工资"],
            "evidence": ["工资流水"],
        },
        headers=_headers(),
    )
    assert document.status_code == 200
    assert document.json()["status"] == "draft"

    laws = client.post(
        "/internal/rag/search-laws",
        json={"query": "拖欠工资", "top_k": 2},
        headers=_headers(),
    )
    assert laws.status_code == 200
    assert len(laws.json()["results"]) == 2
    assert laws.json()["results"][0]["source_id"]

    cases = client.post(
        "/internal/rag/search-cases",
        json={"query": "未签合同", "top_k": 1},
        headers=_headers(),
    )
    assert cases.status_code == 200
    assert len(cases.json()["results"]) == 1

    safety = client.post(
        "/internal/safety/review",
        json={"text": "你一定能胜诉", "source_ids": ["law:labor-dispute-mediation-arbitration:27"]},
        headers=_headers(),
    )
    assert safety.status_code == 200
    assert safety.json()["allowed"] is True
    assert "需要结合证据" in safety.json()["reviewed_text"]
