"""create library items

Revision ID: 0001_create_library_items
Revises:
Create Date: 2026-07-08
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_create_library_items"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "library_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("file_path", sa.String(length=1024), nullable=False),
        sa.Column("markdown_path", sa.String(length=1024), nullable=False),
        sa.Column("imported_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_library_items_id"), "library_items", ["id"], unique=False)
    op.create_index(
        op.f("ix_library_items_original_filename"),
        "library_items",
        ["original_filename"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_library_items_original_filename"), table_name="library_items")
    op.drop_index(op.f("ix_library_items_id"), table_name="library_items")
    op.drop_table("library_items")
