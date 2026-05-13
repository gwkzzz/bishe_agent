from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin, UpdatedAtMixin


class LegalCase(UUIDPrimaryKeyMixin, CreatedAtMixin, UpdatedAtMixin, Base):
    __tablename__ = "legal_cases"
    __table_args__ = (
        Index("ix_legal_cases_user_status", "user_id", "status"),
        Index("ix_legal_cases_user_updated", "user_id", "updated_at"),
    )

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    domain: Mapped[str] = mapped_column(String(64), nullable=False, default="labor_dispute")
    cause: Mapped[str | None] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="open")
    summary: Mapped[str | None] = mapped_column(Text)
    confidence: Mapped[float | None] = mapped_column(Float)

    user: Mapped["User"] = relationship(back_populates="cases")
    facts: Mapped[list["CaseFact"]] = relationship(
        back_populates="case",
        cascade="all, delete-orphan",
    )
    evidence_items: Mapped[list["EvidenceItem"]] = relationship(
        back_populates="case",
        cascade="all, delete-orphan",
    )
    generated_documents: Mapped[list["GeneratedDocument"]] = relationship(
        back_populates="case",
        cascade="all, delete-orphan",
    )
    profile_candidates: Mapped[list["ProfileCandidate"]] = relationship(
        back_populates="case",
        cascade="all, delete-orphan",
    )
    chat_messages: Mapped[list["ChatMessage"]] = relationship(
        back_populates="case",
        cascade="all, delete-orphan",
    )
    async_tasks: Mapped[list["AsyncTask"]] = relationship(
        back_populates="case",
        cascade="all, delete-orphan",
    )


class CaseFact(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "case_facts"
    __table_args__ = (Index("ix_case_facts_case_confirmed", "case_id", "confirmed_by_user"),)

    case_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("legal_cases.id", ondelete="CASCADE"),
        nullable=False,
    )
    fact_text: Mapped[str] = mapped_column(Text, nullable=False)
    occurred_at: Mapped[date | None] = mapped_column(Date)
    source: Mapped[str | None] = mapped_column(String(128))
    confidence: Mapped[float | None] = mapped_column(Float)
    confirmed_by_user: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    case: Mapped[LegalCase] = relationship(back_populates="facts")


class EvidenceItem(UUIDPrimaryKeyMixin, CreatedAtMixin, UpdatedAtMixin, Base):
    __tablename__ = "evidence_items"
    __table_args__ = (
        Index("ix_evidence_items_case_type", "case_id", "evidence_type"),
        Index("ix_evidence_items_case_confirmed", "case_id", "confirmed_by_user"),
    )

    case_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("legal_cases.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    evidence_type: Mapped[str | None] = mapped_column(String(128))
    file_url: Mapped[str | None] = mapped_column(String(1024))
    extracted_text: Mapped[str | None] = mapped_column(Text)
    proves: Mapped[str | None] = mapped_column(Text)
    strength: Mapped[str | None] = mapped_column(String(64))
    risk: Mapped[str | None] = mapped_column(Text)
    confirmed_by_user: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    case: Mapped[LegalCase] = relationship(back_populates="evidence_items")
    async_tasks: Mapped[list["AsyncTask"]] = relationship(back_populates="evidence_item")


class GeneratedDocument(UUIDPrimaryKeyMixin, CreatedAtMixin, UpdatedAtMixin, Base):
    __tablename__ = "generated_documents"
    __table_args__ = (Index("ix_generated_documents_case_type", "case_id", "document_type"),)

    case_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("legal_cases.id", ondelete="CASCADE"),
        nullable=False,
    )
    document_type: Mapped[str] = mapped_column(String(128), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content_md: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="draft")

    case: Mapped[LegalCase] = relationship(back_populates="generated_documents")


class ProfileCandidate(UUIDPrimaryKeyMixin, CreatedAtMixin, UpdatedAtMixin, Base):
    __tablename__ = "profile_candidates"
    __table_args__ = (Index("ix_profile_candidates_case_status", "case_id", "status"),)

    case_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("legal_cases.id", ondelete="CASCADE"),
        nullable=False,
    )
    candidate_type: Mapped[str] = mapped_column(String(64), nullable=False)
    content_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="pending")

    case: Mapped[LegalCase] = relationship(back_populates="profile_candidates")


class ChatMessage(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "chat_messages"
    __table_args__ = (
        Index("ix_chat_messages_case_created", "case_id", "created_at"),
        Index("ix_chat_messages_user_created", "user_id", "created_at"),
    )

    case_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("legal_cases.id", ondelete="CASCADE"),
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    structured_result: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    trace_id: Mapped[str | None] = mapped_column(String(64), index=True)

    case: Mapped[LegalCase | None] = relationship(back_populates="chat_messages")
    user: Mapped["User"] = relationship(back_populates="chat_messages")


class AsyncTask(UUIDPrimaryKeyMixin, CreatedAtMixin, UpdatedAtMixin, Base):
    __tablename__ = "async_tasks"
    __table_args__ = (
        Index("ix_async_tasks_status_type", "status", "task_type"),
        Index("ix_async_tasks_case_created", "case_id", "created_at"),
    )

    case_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("legal_cases.id", ondelete="CASCADE"),
    )
    evidence_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("evidence_items.id", ondelete="SET NULL"),
    )
    task_type: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="pending")
    progress: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    result_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    error_message: Mapped[str | None] = mapped_column(Text)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    case: Mapped[LegalCase | None] = relationship(back_populates="async_tasks")
    evidence_item: Mapped[EvidenceItem | None] = relationship(back_populates="async_tasks")


from app.models.user import User  # noqa: E402
