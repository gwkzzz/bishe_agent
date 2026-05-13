"""initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-05-12
"""

from alembic import op
import sqlalchemy as sa


revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("username", sa.String(length=128), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=True)

    op.create_table(
        "legal_sources",
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("article", sa.String(length=128), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("source_url", sa.String(length=1024), nullable=True),
        sa.Column("milvus_id", sa.String(length=128), nullable=True),
        sa.Column("bm25_doc_id", sa.String(length=128), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_legal_sources_title_article", "legal_sources", ["title", "article"], unique=False)
    op.create_index("ix_legal_sources_status", "legal_sources", ["status"], unique=False)
    op.create_index(op.f("ix_legal_sources_milvus_id"), "legal_sources", ["milvus_id"], unique=False)
    op.create_index(op.f("ix_legal_sources_bm25_doc_id"), "legal_sources", ["bm25_doc_id"], unique=False)

    op.create_table(
        "precedent_cases",
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("cause", sa.String(length=128), nullable=True),
        sa.Column("court", sa.String(length=255), nullable=True),
        sa.Column("key_facts", sa.Text(), nullable=True),
        sa.Column("court_view", sa.Text(), nullable=True),
        sa.Column("source_url", sa.String(length=1024), nullable=True),
        sa.Column("milvus_id", sa.String(length=128), nullable=True),
        sa.Column("bm25_doc_id", sa.String(length=128), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_precedent_cases_cause_court", "precedent_cases", ["cause", "court"], unique=False)
    op.create_index("ix_precedent_cases_title", "precedent_cases", ["title"], unique=False)
    op.create_index(op.f("ix_precedent_cases_milvus_id"), "precedent_cases", ["milvus_id"], unique=False)
    op.create_index(op.f("ix_precedent_cases_bm25_doc_id"), "precedent_cases", ["bm25_doc_id"], unique=False)

    op.create_table(
        "document_templates",
        sa.Column("template_type", sa.String(length=128), nullable=False),
        sa.Column("scene", sa.String(length=128), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("content_md", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("milvus_id", sa.String(length=128), nullable=True),
        sa.Column("bm25_doc_id", sa.String(length=128), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_document_templates_type_scene",
        "document_templates",
        ["template_type", "scene"],
        unique=False,
    )
    op.create_index("ix_document_templates_status", "document_templates", ["status"], unique=False)
    op.create_index(op.f("ix_document_templates_milvus_id"), "document_templates", ["milvus_id"], unique=False)
    op.create_index(
        op.f("ix_document_templates_bm25_doc_id"),
        "document_templates",
        ["bm25_doc_id"],
        unique=False,
    )

    op.create_table(
        "audit_logs",
        sa.Column("trace_id", sa.String(length=64), nullable=False),
        sa.Column("case_id", sa.String(length=36), nullable=True),
        sa.Column("node_name", sa.String(length=128), nullable=True),
        sa.Column("operation", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("input_hash", sa.String(length=128), nullable=True),
        sa.Column("output_hash", sa.String(length=128), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_logs_trace_created", "audit_logs", ["trace_id", "created_at"], unique=False)
    op.create_index("ix_audit_logs_case_node", "audit_logs", ["case_id", "node_name"], unique=False)

    op.create_table(
        "legal_cases",
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("domain", sa.String(length=64), nullable=False),
        sa.Column("cause", sa.String(length=128), nullable=True),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_legal_cases_user_status", "legal_cases", ["user_id", "status"], unique=False)
    op.create_index("ix_legal_cases_user_updated", "legal_cases", ["user_id", "updated_at"], unique=False)

    op.create_table(
        "case_facts",
        sa.Column("case_id", sa.String(length=36), nullable=False),
        sa.Column("fact_text", sa.Text(), nullable=False),
        sa.Column("occurred_at", sa.Date(), nullable=True),
        sa.Column("source", sa.String(length=128), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("confirmed_by_user", sa.Boolean(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["legal_cases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_case_facts_case_confirmed", "case_facts", ["case_id", "confirmed_by_user"], unique=False)

    op.create_table(
        "evidence_items",
        sa.Column("case_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("evidence_type", sa.String(length=128), nullable=True),
        sa.Column("file_url", sa.String(length=1024), nullable=True),
        sa.Column("extracted_text", sa.Text(), nullable=True),
        sa.Column("proves", sa.Text(), nullable=True),
        sa.Column("strength", sa.String(length=64), nullable=True),
        sa.Column("risk", sa.Text(), nullable=True),
        sa.Column("confirmed_by_user", sa.Boolean(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["legal_cases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_evidence_items_case_type", "evidence_items", ["case_id", "evidence_type"], unique=False)
    op.create_index("ix_evidence_items_case_confirmed", "evidence_items", ["case_id", "confirmed_by_user"], unique=False)

    op.create_table(
        "generated_documents",
        sa.Column("case_id", sa.String(length=36), nullable=False),
        sa.Column("document_type", sa.String(length=128), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("content_md", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["legal_cases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_generated_documents_case_type",
        "generated_documents",
        ["case_id", "document_type"],
        unique=False,
    )

    op.create_table(
        "profile_candidates",
        sa.Column("case_id", sa.String(length=36), nullable=False),
        sa.Column("candidate_type", sa.String(length=64), nullable=False),
        sa.Column("content_json", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["legal_cases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_profile_candidates_case_status", "profile_candidates", ["case_id", "status"], unique=False)

    op.create_table(
        "chat_messages",
        sa.Column("case_id", sa.String(length=36), nullable=True),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("structured_result", sa.JSON(), nullable=True),
        sa.Column("trace_id", sa.String(length=64), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["legal_cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_chat_messages_case_created", "chat_messages", ["case_id", "created_at"], unique=False)
    op.create_index("ix_chat_messages_user_created", "chat_messages", ["user_id", "created_at"], unique=False)
    op.create_index(op.f("ix_chat_messages_trace_id"), "chat_messages", ["trace_id"], unique=False)

    op.create_table(
        "async_tasks",
        sa.Column("case_id", sa.String(length=36), nullable=True),
        sa.Column("evidence_id", sa.String(length=36), nullable=True),
        sa.Column("task_type", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("progress", sa.Integer(), nullable=False),
        sa.Column("result_json", sa.JSON(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False),
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["legal_cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["evidence_id"], ["evidence_items.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_async_tasks_status_type", "async_tasks", ["status", "task_type"], unique=False)
    op.create_index("ix_async_tasks_case_created", "async_tasks", ["case_id", "created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_async_tasks_case_created", table_name="async_tasks")
    op.drop_index("ix_async_tasks_status_type", table_name="async_tasks")
    op.drop_table("async_tasks")
    op.drop_index(op.f("ix_chat_messages_trace_id"), table_name="chat_messages")
    op.drop_index("ix_chat_messages_user_created", table_name="chat_messages")
    op.drop_index("ix_chat_messages_case_created", table_name="chat_messages")
    op.drop_table("chat_messages")
    op.drop_index("ix_profile_candidates_case_status", table_name="profile_candidates")
    op.drop_table("profile_candidates")
    op.drop_index("ix_generated_documents_case_type", table_name="generated_documents")
    op.drop_table("generated_documents")
    op.drop_index("ix_evidence_items_case_confirmed", table_name="evidence_items")
    op.drop_index("ix_evidence_items_case_type", table_name="evidence_items")
    op.drop_table("evidence_items")
    op.drop_index("ix_case_facts_case_confirmed", table_name="case_facts")
    op.drop_table("case_facts")
    op.drop_index("ix_legal_cases_user_updated", table_name="legal_cases")
    op.drop_index("ix_legal_cases_user_status", table_name="legal_cases")
    op.drop_table("legal_cases")
    op.drop_index("ix_audit_logs_case_node", table_name="audit_logs")
    op.drop_index("ix_audit_logs_trace_created", table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_index(op.f("ix_precedent_cases_bm25_doc_id"), table_name="precedent_cases")
    op.drop_index(op.f("ix_precedent_cases_milvus_id"), table_name="precedent_cases")
    op.drop_index("ix_precedent_cases_title", table_name="precedent_cases")
    op.drop_index("ix_precedent_cases_cause_court", table_name="precedent_cases")
    op.drop_table("precedent_cases")
    op.drop_index(op.f("ix_document_templates_bm25_doc_id"), table_name="document_templates")
    op.drop_index(op.f("ix_document_templates_milvus_id"), table_name="document_templates")
    op.drop_index("ix_document_templates_status", table_name="document_templates")
    op.drop_index("ix_document_templates_type_scene", table_name="document_templates")
    op.drop_table("document_templates")
    op.drop_index(op.f("ix_legal_sources_bm25_doc_id"), table_name="legal_sources")
    op.drop_index(op.f("ix_legal_sources_milvus_id"), table_name="legal_sources")
    op.drop_index("ix_legal_sources_status", table_name="legal_sources")
    op.drop_index("ix_legal_sources_title_article", table_name="legal_sources")
    op.drop_table("legal_sources")
    op.drop_index(op.f("ix_users_username"), table_name="users")
    op.drop_table("users")
