from __future__ import annotations

import json
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session


class CaseRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_case_summary(self, case_id: str) -> dict[str, Any] | None:
        row = self.db.execute(
            text(
                """
                SELECT id, user_id, title, domain, cause, status, summary, confidence
                FROM legal_cases
                WHERE id = :case_id
                """
            ),
            {"case_id": case_id},
        ).mappings().first()
        return dict(row) if row else None

    def list_case_facts(self, case_id: str) -> list[dict[str, Any]]:
        rows = self.db.execute(
            text(
                """
                SELECT id, fact_text, occurred_at, source, confidence, confirmed_by_user
                FROM case_facts
                WHERE case_id = :case_id
                ORDER BY occurred_at IS NULL, occurred_at, created_at
                """
            ),
            {"case_id": case_id},
        ).mappings()
        return [dict(row) for row in rows]

    def create_profile_candidate(
        self,
        case_id: str,
        candidate_type: str,
        content_json: dict[str, Any],
        status: str = "pending",
    ) -> None:
        self.db.execute(
            text(
                """
                INSERT INTO profile_candidates
                    (id, case_id, candidate_type, content_json, status, created_at, updated_at)
                VALUES
                    (UUID(), :case_id, :candidate_type, :content_json, :status, NOW(), NOW())
                """
            ),
            {
                "case_id": case_id,
                "candidate_type": candidate_type,
                "content_json": json.dumps(content_json, ensure_ascii=False, default=str),
                "status": status,
            },
        )
