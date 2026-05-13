from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session


class TemplateRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_template_text(self, template_type: str, scene: str | None = None) -> str | None:
        filters = ["template_type = :template_type"]
        params = {"template_type": template_type, "scene": scene}
        if scene:
            filters.append("scene = :scene")

        row = self.db.execute(
            text(
                f"""
                SELECT content_md
                FROM document_templates
                WHERE {" AND ".join(filters)}
                  AND status = 'active'
                ORDER BY id
                LIMIT 1
                """
            ),
            params,
        ).mappings().first()
        return row["content_md"] if row else None
