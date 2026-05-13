from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

from app.retrieval.tokenizer import joined_text


DATA_DIR = Path(__file__).resolve().parent / "data"
KNOWLEDGE_FILE = DATA_DIR / "labor_knowledge.json"

CollectionName = Literal[
    "labor_law",
    "labor_precedent",
    "labor_template",
    "labor_limitation_rule",
]


@dataclass(frozen=True)
class KnowledgeDocument:
    source_id: str
    title: str
    text: str
    collection: CollectionName
    source_url: str | None = None
    article: str | None = None
    status: str | None = None
    metadata: dict[str, Any] | None = None

    @property
    def search_text(self) -> str:
        metadata = self.metadata or {}
        return joined_text(
            [
                self.title,
                self.article,
                self.text,
                " ".join(str(item) for item in metadata.get("topics", [])),
                str(metadata.get("cause") or ""),
                str(metadata.get("court") or ""),
            ]
        )


@lru_cache
def load_knowledge_file() -> dict[str, Any]:
    with KNOWLEDGE_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def load_seed_documents(collection: CollectionName) -> list[KnowledgeDocument]:
    payload = load_knowledge_file()
    if collection == "labor_law":
        return [_law_document(item) for item in payload.get("legal_sources", [])]
    if collection == "labor_precedent":
        return [_precedent_document(item) for item in payload.get("precedent_cases", [])]
    if collection == "labor_template":
        return [_template_document(item) for item in payload.get("document_templates", [])]
    if collection == "labor_limitation_rule":
        return [_rule_document(item) for item in payload.get("limitation_rules", [])]
    return []


def load_all_seed_documents() -> list[KnowledgeDocument]:
    documents: list[KnowledgeDocument] = []
    for collection in (
        "labor_law",
        "labor_precedent",
        "labor_template",
        "labor_limitation_rule",
    ):
        documents.extend(load_seed_documents(collection))
    return documents


def _law_document(item: dict[str, Any]) -> KnowledgeDocument:
    metadata = {
        "article": item.get("article"),
        "status": item.get("status"),
        "topics": item.get("topics", []),
        "raw_type": "legal_source",
    }
    return KnowledgeDocument(
        source_id=item["source_id"],
        title=item["title"],
        article=item.get("article"),
        text=item["content"],
        collection="labor_law",
        source_url=item.get("source_url"),
        status=item.get("status"),
        metadata=metadata,
    )


def _precedent_document(item: dict[str, Any]) -> KnowledgeDocument:
    metadata = {
        "cause": item.get("cause"),
        "court": item.get("court"),
        "key_facts": item.get("key_facts"),
        "court_view": item.get("court_view"),
        "similarities": item.get("similarities", []),
        "differences": item.get("differences", []),
        "raw_type": "precedent_case",
    }
    return KnowledgeDocument(
        source_id=item["source_id"],
        title=item["title"],
        text=joined_text([item.get("key_facts"), item.get("court_view")]),
        collection="labor_precedent",
        source_url=item.get("source_url"),
        status="active",
        metadata=metadata,
    )


def _template_document(item: dict[str, Any]) -> KnowledgeDocument:
    metadata = {
        "template_type": item.get("template_type"),
        "scene": item.get("scene"),
        "topics": item.get("topics", []),
        "raw_type": "document_template",
    }
    return KnowledgeDocument(
        source_id=item["source_id"],
        title=item["title"],
        text=item["content_md"],
        collection="labor_template",
        source_url=item.get("source_url"),
        status=item.get("status"),
        metadata=metadata,
    )


def _rule_document(item: dict[str, Any]) -> KnowledgeDocument:
    metadata = {
        "source_ref": item.get("source_ref"),
        "topics": item.get("topics", []),
        "raw_type": "limitation_rule",
    }
    return KnowledgeDocument(
        source_id=item["source_id"],
        title=item["title"],
        text=item["content"],
        collection="labor_limitation_rule",
        source_url=item.get("source_url"),
        status=item.get("status"),
        metadata=metadata,
    )
