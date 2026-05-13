from __future__ import annotations

import json
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session


class AuditLogger:
    def __init__(self, db: Session) -> None:
        self.db = db

    def log(
        self,
        trace_id: str,
        operation: str,
        status: str,
        case_id: str | None = None,
        node_name: str | None = None,
        input_hash: str | None = None,
        output_hash: str | None = None,
        latency_ms: int | None = None,
        error_message: str | None = None,
        metadata_json: dict[str, Any] | None = None,
    ) -> None:
        self.db.execute(
            text(
                """
                INSERT INTO audit_logs
                    (id, trace_id, case_id, node_name, operation, status,
                     input_hash, output_hash, latency_ms, error_message,
                     metadata_json, created_at)
                VALUES
                    (UUID(), :trace_id, :case_id, :node_name, :operation, :status,
                     :input_hash, :output_hash, :latency_ms, :error_message,
                     :metadata_json, NOW())
                """
            ),
            {
                "trace_id": trace_id,
                "case_id": case_id,
                "node_name": node_name,
                "operation": operation,
                "status": status,
                "input_hash": input_hash,
                "output_hash": output_hash,
                "latency_ms": latency_ms,
                "error_message": error_message,
                "metadata_json": (
                    json.dumps(metadata_json, ensure_ascii=False, default=str)
                    if metadata_json is not None
                    else None
                ),
            },
        )
