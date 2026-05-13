from __future__ import annotations

import argparse
import sys
import uuid
from collections import defaultdict
from pathlib import Path
from typing import Any

from sqlalchemy import text


ALGORITHM_ROOT = Path(__file__).resolve().parents[1]
if str(ALGORITHM_ROOT) not in sys.path:
    sys.path.insert(0, str(ALGORITHM_ROOT))

from app.core.config import get_settings  # noqa: E402
from app.core.database import DatabaseSession  # noqa: E402
from app.integrations.milvus_client import MilvusClient  # noqa: E402
from app.retrieval.corpus import KnowledgeDocument, load_all_seed_documents, load_knowledge_file  # noqa: E402
from app.retrieval.tokenizer import stable_embedding  # noqa: E402


VECTOR_COLLECTIONS = {
    "labor_law": "labor_law_chunks",
    "labor_limitation_rule": "labor_law_chunks",
    "labor_precedent": "labor_precedent_chunks",
    "labor_template": "labor_template_chunks",
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Import M5 labor RAG knowledge base.")
    parser.add_argument("--skip-db", action="store_true", help="Only validate seed data.")
    parser.add_argument(
        "--with-milvus",
        action="store_true",
        help="Also rebuild/upsert Milvus chunk collections.",
    )
    parser.add_argument(
        "--drop-vector",
        action="store_true",
        help="Drop Milvus collections before inserting vectors.",
    )
    args = parser.parse_args()

    payload = load_knowledge_file()
    documents = load_all_seed_documents()
    _validate_documents(documents)

    if not args.skip_db:
        counts = _upsert_database(payload)
        print(f"database upserted: {counts}")

    if args.with_milvus:
        counts = _upsert_milvus(documents, drop_existing=args.drop_vector)
        print(f"milvus upserted: {counts}")

    if args.skip_db and not args.with_milvus:
        print(f"validated {len(documents)} knowledge documents")


def _upsert_database(payload: dict[str, Any]) -> dict[str, int]:
    counts = {"legal_sources": 0, "precedent_cases": 0, "document_templates": 0}
    with DatabaseSession().session() as db:
        for item in payload.get("legal_sources", []):
            db.execute(
                text(
                    """
                    INSERT INTO legal_sources
                        (id, title, article, content, status, source_url, bm25_doc_id,
                         created_at, updated_at)
                    VALUES
                        (:id, :title, :article, :content, :status, :source_url, :bm25_doc_id,
                         NOW(), NOW())
                    ON DUPLICATE KEY UPDATE
                        title = VALUES(title),
                        article = VALUES(article),
                        content = VALUES(content),
                        status = VALUES(status),
                        source_url = VALUES(source_url),
                        bm25_doc_id = VALUES(bm25_doc_id),
                        updated_at = NOW()
                    """
                ),
                {
                    "id": _db_id(item["source_id"]),
                    "title": item["title"],
                    "article": item.get("article"),
                    "content": item["content"],
                    "status": item.get("status", "effective"),
                    "source_url": item.get("source_url"),
                    "bm25_doc_id": item["source_id"],
                },
            )
            counts["legal_sources"] += 1

        for item in payload.get("precedent_cases", []):
            db.execute(
                text(
                    """
                    INSERT INTO precedent_cases
                        (id, title, cause, court, key_facts, court_view, source_url,
                         bm25_doc_id, created_at, updated_at)
                    VALUES
                        (:id, :title, :cause, :court, :key_facts, :court_view, :source_url,
                         :bm25_doc_id, NOW(), NOW())
                    ON DUPLICATE KEY UPDATE
                        title = VALUES(title),
                        cause = VALUES(cause),
                        court = VALUES(court),
                        key_facts = VALUES(key_facts),
                        court_view = VALUES(court_view),
                        source_url = VALUES(source_url),
                        bm25_doc_id = VALUES(bm25_doc_id),
                        updated_at = NOW()
                    """
                ),
                {
                    "id": _db_id(item["source_id"]),
                    "title": item["title"],
                    "cause": item.get("cause"),
                    "court": item.get("court"),
                    "key_facts": item.get("key_facts"),
                    "court_view": item.get("court_view"),
                    "source_url": item.get("source_url"),
                    "bm25_doc_id": item["source_id"],
                },
            )
            counts["precedent_cases"] += 1

        for item in payload.get("document_templates", []):
            db.execute(
                text(
                    """
                    INSERT INTO document_templates
                        (id, template_type, scene, title, content_md, status, bm25_doc_id,
                         created_at, updated_at)
                    VALUES
                        (:id, :template_type, :scene, :title, :content_md, :status,
                         :bm25_doc_id, NOW(), NOW())
                    ON DUPLICATE KEY UPDATE
                        template_type = VALUES(template_type),
                        scene = VALUES(scene),
                        title = VALUES(title),
                        content_md = VALUES(content_md),
                        status = VALUES(status),
                        bm25_doc_id = VALUES(bm25_doc_id),
                        updated_at = NOW()
                    """
                ),
                {
                    "id": _db_id(item["source_id"]),
                    "template_type": item["template_type"],
                    "scene": item.get("scene"),
                    "title": item["title"],
                    "content_md": item["content_md"],
                    "status": item.get("status", "active"),
                    "bm25_doc_id": item["source_id"],
                },
            )
            counts["document_templates"] += 1
    return counts


def _upsert_milvus(
    documents: list[KnowledgeDocument],
    *,
    drop_existing: bool,
) -> dict[str, int]:
    settings = get_settings()
    milvus = MilvusClient()
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for document in documents:
        collection_name = VECTOR_COLLECTIONS[document.collection]
        grouped[collection_name].append(
            {
                "pk": _vector_id(document.source_id),
                "source_id": document.source_id,
                "title": document.title,
                "article": document.article or "",
                "text": document.text,
                "source_url": document.source_url or "",
                "metadata_json": {
                    **(document.metadata or {}),
                    "status": document.status,
                    "collection": document.collection,
                },
                "embedding": stable_embedding(
                    document.search_text,
                    dimension=settings.rag_vector_dimension,
                ),
            }
        )

    counts: dict[str, int] = {}
    for collection_name, rows in grouped.items():
        counts[collection_name] = milvus.upsert(
            collection_name,
            rows,
            dimension=settings.rag_vector_dimension,
            drop_existing=drop_existing,
        )
    return counts


def _validate_documents(documents: list[KnowledgeDocument]) -> None:
    seen: set[str] = set()
    for document in documents:
        if not document.source_id:
            raise ValueError(f"{document.title} is missing source_id")
        if document.source_id in seen:
            raise ValueError(f"duplicate source_id: {document.source_id}")
        seen.add(document.source_id)
        if document.collection in ("labor_law", "labor_precedent") and not (
            document.source_id or document.source_url
        ):
            raise ValueError(f"{document.title} is missing traceable source")
        if document.collection == "labor_law" and document.status != "effective":
            raise ValueError(f"{document.source_id} is not effective")


def _db_id(source_id: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, source_id))


def _vector_id(source_id: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"milvus:{source_id}"))


if __name__ == "__main__":
    main()
