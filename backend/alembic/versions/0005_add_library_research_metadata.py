"""add library research metadata

Revision ID: 0005_add_library_research_metadata
Revises: 0004_add_library_project_id
Create Date: 2026-07-12
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0005_add_library_research_metadata"
down_revision: str | None = "0004_add_library_project_id"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("library_items", sa.Column("publisher", sa.String(length=512), nullable=True))
    op.add_column("library_items", sa.Column("source_url", sa.String(length=1024), nullable=True))
    op.add_column(
        "library_items", sa.Column("metadata_source", sa.String(length=64), nullable=True)
    )
    op.add_column(
        "library_items", sa.Column("metadata_confidence", sa.String(length=32), nullable=True)
    )
    op.add_column(
        "library_items", sa.Column("metadata_updated_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "library_items",
        sa.Column("reading_progress", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column("library_items", sa.Column("importance", sa.String(length=32), nullable=True))
    op.add_column("library_items", sa.Column("priority", sa.String(length=32), nullable=True))
    op.add_column("library_items", sa.Column("domain", sa.String(length=128), nullable=True))
    op.add_column("library_items", sa.Column("method", sa.String(length=128), nullable=True))
    op.add_column("library_items", sa.Column("difficulty", sa.String(length=32), nullable=True))
    op.add_column("library_items", sa.Column("personal_tags", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("library_items", "personal_tags")
    op.drop_column("library_items", "difficulty")
    op.drop_column("library_items", "method")
    op.drop_column("library_items", "domain")
    op.drop_column("library_items", "priority")
    op.drop_column("library_items", "importance")
    op.drop_column("library_items", "reading_progress")
    op.drop_column("library_items", "metadata_updated_at")
    op.drop_column("library_items", "metadata_confidence")
    op.drop_column("library_items", "metadata_source")
    op.drop_column("library_items", "source_url")
    op.drop_column("library_items", "publisher")
