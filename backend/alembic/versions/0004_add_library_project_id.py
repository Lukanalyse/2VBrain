"""add library project id

Revision ID: 0004_add_library_project_id
Revises: 0003_add_library_collection_status
Create Date: 2026-07-12
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0004_add_library_project_id"
down_revision: str | None = "0003_add_library_collection_status"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "library_items",
        sa.Column("project_id", sa.String(length=512), nullable=True),
    )
    op.create_index(
        "ix_library_items_project_id",
        "library_items",
        ["project_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_library_items_project_id", table_name="library_items")
    op.drop_column("library_items", "project_id")
