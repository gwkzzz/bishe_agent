from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app
from app.retrieval.corpus import load_all_seed_documents
from app.retrieval.hybrid import get_hybrid_search_service


def _headers(trace_id: str = "test-trace-m5") -> dict[str, str]:
    settings = get_settings()
    return {
        "X-Internal-Token": settings.algorithm_internal_token,
        settings.trace_header_name: trace_id,
    }


def test_m5_law_search_returns_traceable_reranked_sources() -> None:
    response = TestClient(app).post(
        "/internal/rag/search-laws",
        json={"query": "公司拖欠工资两个月，工资流水能证明吗", "top_k": 3},
        headers=_headers(),
    )

    assert response.status_code == 200
    results = response.json()["results"]
    assert results
    assert all(item["source_id"] or item["source_url"] for item in results)
    assert all(item["metadata"]["source_verified"] for item in results)
    assert any(item["article"] == "第三十条" for item in results)
    assert "mock" not in results[0]["metadata"]
    assert results[0]["score"] >= results[-1]["score"]


def test_m5_case_search_returns_precedent_metadata() -> None:
    response = TestClient(app).post(
        "/internal/rag/search-cases",
        json={"query": "未签书面劳动合同二倍工资", "top_k": 2},
        headers=_headers(),
    )

    assert response.status_code == 200
    results = response.json()["results"]
    assert results
    assert all(item["source_id"] for item in results)
    assert any("未" in item["title"] or item["cause"] == "劳动合同纠纷" for item in results)
    assert results[0]["metadata"]["retrieval_channels"]


def test_m5_filters_low_relevance_queries() -> None:
    response = TestClient(app).post(
        "/internal/rag/search-laws",
        json={"query": "量子火箭外卖积分", "top_k": 5},
        headers=_headers(),
    )

    assert response.status_code == 200
    assert response.json()["results"] == []


def test_m5_template_bm25_index_is_available() -> None:
    results = get_hybrid_search_service().search_templates("劳动仲裁申请书 证据目录", top_k=2)

    assert results
    assert results[0].collection == "labor_template"
    assert results[0].source_id.startswith("template:")


def test_m5_seed_documents_have_unique_traceable_ids() -> None:
    documents = load_all_seed_documents()
    source_ids = [document.source_id for document in documents]

    assert len(source_ids) == len(set(source_ids))
    assert all(document.source_id for document in documents)
