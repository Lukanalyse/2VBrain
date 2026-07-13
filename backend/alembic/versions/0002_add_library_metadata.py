"""add library metadata

Revision ID: 0002_add_library_metadata
Revises: 0001_create_library_items
Create Date: 2026-07-08
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_add_library_metadata"
down_revision: str | None = "0001_create_library_items"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("library_items", sa.Column("title", sa.String(length=512), nullable=True))
    op.add_column("library_items", sa.Column("authors", sa.Text(), nullable=True))
    op.add_column("library_items", sa.Column("journal", sa.String(length=512), nullable=True))
    op.add_column("library_items", sa.Column("conference", sa.String(length=512), nullable=True))
    op.add_column("library_items", sa.Column("year", sa.Integer(), nullable=True))
    op.add_column("library_items", sa.Column("doi", sa.String(length=255), nullable=True))
    op.add_column("library_items", sa.Column("abstract", sa.Text(), nullable=True))
    op.add_column("library_items", sa.Column("keywords", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("library_items", "keywords")
    op.drop_column("library_items", "abstract")
    op.drop_column("library_items", "doi")
    op.drop_column("library_items", "year")
    op.drop_column("library_items", "conference")
    op.drop_column("library_items", "journal")
    op.drop_column("library_items", "authors")
    op.drop_column("library_items", "title")
