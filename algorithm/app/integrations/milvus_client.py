from __future__ import annotations

import json
from typing import Any

from pymilvus import Collection, CollectionSchema, DataType, FieldSchema, connections, utility

from app.core.config import get_settings
from app.integrations.errors import VectorStoreError


class MilvusClient:
    def __init__(self, alias: str = "default") -> None:
        settings = get_settings()
        self.alias = alias
        self.host = settings.milvus_host
        self.port = settings.milvus_port

    def connect(self) -> None:
        try:
            connections.connect(alias=self.alias, host=self.host, port=str(self.port))
        except Exception as exc:
            raise VectorStoreError("Unable to connect to Milvus") from exc

    def ensure_collection(
        self,
        collection_name: str,
        *,
        dimension: int,
        drop_existing: bool = False,
    ) -> None:
        try:
            self.connect()
            if drop_existing and utility.has_collection(collection_name, using=self.alias):
                utility.drop_collection(collection_name, using=self.alias)
            if utility.has_collection(collection_name, using=self.alias):
                return

            fields = [
                FieldSchema(
                    name="pk",
                    dtype=DataType.VARCHAR,
                    is_primary=True,
                    max_length=128,
                ),
                FieldSchema(name="source_id", dtype=DataType.VARCHAR, max_length=256),
                FieldSchema(name="title", dtype=DataType.VARCHAR, max_length=512),
                FieldSchema(name="article", dtype=DataType.VARCHAR, max_length=128),
                FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=8192),
                FieldSchema(name="source_url", dtype=DataType.VARCHAR, max_length=1024),
                FieldSchema(name="metadata_json", dtype=DataType.VARCHAR, max_length=4096),
                FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=dimension),
            ]
            schema = CollectionSchema(fields=fields, description=f"{collection_name} RAG chunks")
            collection = Collection(collection_name, schema=schema, using=self.alias)
            collection.create_index(
                field_name="embedding",
                index_params={
                    "index_type": "AUTOINDEX",
                    "metric_type": "COSINE",
                    "params": {},
                },
            )
        except Exception as exc:
            raise VectorStoreError(f"Unable to ensure Milvus collection {collection_name}") from exc

    def upsert(
        self,
        collection_name: str,
        rows: list[dict[str, Any]],
        *,
        dimension: int,
        drop_existing: bool = False,
    ) -> int:
        if not rows:
            return 0
        try:
            self.ensure_collection(
                collection_name,
                dimension=dimension,
                drop_existing=drop_existing,
            )
            collection = Collection(collection_name, using=self.alias)
            normalized_rows = [_normalize_row(row) for row in rows]
            collection.upsert(normalized_rows)
            collection.flush()
            return len(normalized_rows)
        except Exception as exc:
            raise VectorStoreError(f"Milvus upsert failed for {collection_name}") from exc

    def search(
        self,
        collection_name: str,
        vector: list[float],
        vector_field: str = "embedding",
        limit: int = 10,
        output_fields: list[str] | None = None,
        search_params: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        try:
            self.connect()
            collection = Collection(collection_name, using=self.alias)
            collection.load()
            results = collection.search(
                data=[vector],
                anns_field=vector_field,
                param=search_params or {"metric_type": "COSINE", "params": {"nprobe": 10}},
                limit=limit,
                output_fields=output_fields
                or ["source_id", "title", "article", "text", "source_url", "metadata_json"],
            )
            return [
                {
                    "id": hit.id,
                    "score": hit.score,
                    "entity": _entity_to_dict(hit, output_fields),
                }
                for hit in results[0]
            ]
        except Exception as exc:
            raise VectorStoreError(f"Milvus search failed for {collection_name}") from exc


def _normalize_row(row: dict[str, Any]) -> dict[str, Any]:
    metadata = row.get("metadata_json")
    if isinstance(metadata, dict):
        metadata = json.dumps(metadata, ensure_ascii=False, default=str)
    return {
        "pk": str(row.get("pk") or row.get("source_id"))[:128],
        "source_id": str(row.get("source_id") or "")[:256],
        "title": str(row.get("title") or "")[:512],
        "article": str(row.get("article") or "")[:128],
        "text": str(row.get("text") or "")[:8192],
        "source_url": str(row.get("source_url") or "")[:1024],
        "metadata_json": str(metadata or "")[:4096],
        "embedding": row["embedding"],
    }


def _entity_to_dict(hit: Any, output_fields: list[str] | None) -> dict[str, Any]:
    fields = output_fields or ["source_id", "title", "article", "text", "source_url", "metadata_json"]
    entity: dict[str, Any] = {}
    for field in fields:
        try:
            entity[field] = hit.entity.get(field)
        except Exception:
            entity[field] = None
    return entity
