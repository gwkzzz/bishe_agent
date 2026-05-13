from __future__ import annotations

from app.retrieval.hybrid import get_hybrid_search_service
from app.retrieval.types import RetrievalResult
from app.schemas.internal import LegalBasis, PrecedentReference


def search_law_basis(
    query: str,
    *,
    top_k: int = 5,
    trace_id: str | None = None,
    case_id: str | None = None,
) -> list[LegalBasis]:
    results = get_hybrid_search_service().search_laws(
        query,
        top_k=top_k,
        trace_id=trace_id,
        case_id=case_id,
    )
    return [_to_legal_basis(item) for item in results]


def search_precedent_references(
    query: str,
    *,
    top_k: int = 5,
    trace_id: str | None = None,
    case_id: str | None = None,
) -> list[PrecedentReference]:
    results = get_hybrid_search_service().search_precedents(
        query,
        top_k=top_k,
        trace_id=trace_id,
        case_id=case_id,
    )
    return [_to_precedent_reference(item) for item in results]


def _to_legal_basis(item: RetrievalResult) -> LegalBasis:
    metadata = item.metadata or {}
    return LegalBasis(
        source_id=item.source_id,
        title=item.title,
        article=item.article or metadata.get("article"),
        summary=_snippet(item.text),
        source_url=item.source_url,
        score=item.score,
        verified=bool(metadata.get("source_verified") or item.source_id or item.source_url),
        metadata=metadata,
    )


def _to_precedent_reference(item: RetrievalResult) -> PrecedentReference:
    metadata = item.metadata or {}
    return PrecedentReference(
        source_id=item.source_id,
        title=item.title,
        cause=metadata.get("cause"),
        court=metadata.get("court"),
        summary=_snippet(item.text),
        similarities=[str(value) for value in metadata.get("similarities", [])],
        differences=[str(value) for value in metadata.get("differences", [])],
        source_url=item.source_url,
        score=item.score,
        verified=bool(metadata.get("source_verified") or item.source_id or item.source_url),
        metadata=metadata,
    )


def _snippet(text: str, limit: int = 180) -> str:
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    return f"{compact[: limit - 3]}..."
