"""add assistant derived index

Revision ID: 0006_add_assistant_index
Revises: 0005_add_library_research_metadata
Create Date: 2026-07-14
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0006_add_assistant_index"
down_revision: str | None = "0005_add_library_research_metadata"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "assistant_documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_key", sa.String(length=2048), nullable=False, unique=True),
        sa.Column("object_id", sa.String(length=512), nullable=False),
        sa.Column("object_type", sa.String(length=32), nullable=False),
        sa.Column("object_title", sa.String(length=512), nullable=False),
        sa.Column("object_subtitle", sa.String(length=512), nullable=False),
        sa.Column("object_markdown_path", sa.String(length=2048), nullable=False),
        sa.Column("source_kind", sa.String(length=32), nullable=False),
        sa.Column("source_title", sa.String(length=512), nullable=False),
        sa.Column("source_path", sa.String(length=2048), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("embedding_model", sa.String(length=255), nullable=False),
        sa.Column("indexed_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_assistant_documents_object_id", "assistant_documents", ["object_id"])
    op.create_table(
        "assistant_chunks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("document_id", sa.Integer(), sa.ForeignKey("assistant_documents.id")),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("heading", sa.String(length=512), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", sa.LargeBinary(), nullable=False),
        sa.Column("embedding_dimensions", sa.Integer(), nullable=False),
        sa.UniqueConstraint("document_id", "ordinal", name="uq_assistant_chunk_ordinal"),
    )
    op.create_table(
        "assistant_project_documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.String(length=512), nullable=False),
        sa.Column("document_id", sa.Integer(), sa.ForeignKey("assistant_documents.id")),
        sa.UniqueConstraint("project_id", "document_id", name="uq_assistant_project_document"),
    )
    op.execute(
        "CREATE VIRTUAL TABLE assistant_chunks_fts "
        "USING fts5(chunk_id UNINDEXED, content, tokenize='unicode61 remove_diacritics 2')"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS assistant_chunks_fts")
    op.drop_table("assistant_project_documents")
    op.drop_table("assistant_chunks")
    op.drop_table("assistant_documents")
