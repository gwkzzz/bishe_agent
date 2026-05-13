from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session


class EvidenceRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_evidence_for_case(self, case_id: str) -> list[dict[str, Any]]:
        rows = self.db.execute(
            text(
                """
                SELECT id, name, evidence_type, file_url, extracted_text, proves,
                       strength, risk, confirmed_by_user
                FROM evidence_items
                WHERE case_id = :case_id
                ORDER BY created_at
                """
            ),
            {"case_id": case_id},
        ).mappings()
        return [dict(row) for row in rows]

    def update_analysis(
        self,
        evidence_id: str,
        extracted_text: str | None,
        proves: str | None,
        strength: str | None,
        risk: str | None,
    ) -> None:
        self.db.execute(
            text(
                """
                UPDATE evidence_items
                SET extracted_text = :extracted_text,
                    proves = :proves,
                    strength = :strength,
                    risk = :risk,
                    updated_at = NOW()
                WHERE id = :evidence_id
                """
            ),
            {
                "evidence_id": evidence_id,
                "extracted_text": extracted_text,
                "proves": proves,
                "strength": strength,
                "risk": risk,
            },
        )
