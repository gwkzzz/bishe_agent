from __future__ import annotations

from sqlalchemy import Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin, UpdatedAtMixin


class LegalSource(UUIDPrimaryKeyMixin, CreatedAtMixin, UpdatedAtMixin, Base):
    __tablename__ = "legal_sources"
    __table_args__ = (
        Index("ix_legal_sources_title_article", "title", "article"),
        Index("ix_legal_sources_status", "status"),
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    article: Mapped[str | None] = mapped_column(String(128))
    content: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="effective")
    source_url: Mapped[str | None] = mapped_column(String(1024))
    milvus_id: Mapped[str | None] = mapped_column(String(128), index=True)
    bm25_doc_id: Mapped[str | None] = mapped_column(String(128), index=True)


class PrecedentCase(UUIDPrimaryKeyMixin, CreatedAtMixin, UpdatedAtMixin, Base):
    __tablename__ = "precedent_cases"
    __table_args__ = (
        Index("ix_precedent_cases_cause_court", "cause", "court"),
        Index("ix_precedent_cases_title", "title"),
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    cause: Mapped[str | None] = mapped_column(String(128))
    court: Mapped[str | None] = mapped_column(String(255))
    key_facts: Mapped[str | None] = mapped_column(Text)
    court_view: Mapped[str | None] = mapped_column(Text)
    source_url: Mapped[str | None] = mapped_column(String(1024))
    milvus_id: Mapped[str | None] = mapped_column(String(128), index=True)
    bm25_doc_id: Mapped[str | None] = mapped_column(String(128), index=True)


class DocumentTemplate(UUIDPrimaryKeyMixin, CreatedAtMixin, UpdatedAtMixin, Base):
    __tablename__ = "document_templates"
    __table_args__ = (
        Index("ix_document_templates_type_scene", "template_type", "scene"),
        Index("ix_document_templates_status", "status"),
    )

    template_type: Mapped[str] = mapped_column(String(128), nullable=False)
    scene: Mapped[str | None] = mapped_column(String(128))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content_md: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="active")
    milvus_id: Mapped[str | None] = mapped_column(String(128), index=True)
    bm25_doc_id: Mapped[str | None] = mapped_column(String(128), index=True)
