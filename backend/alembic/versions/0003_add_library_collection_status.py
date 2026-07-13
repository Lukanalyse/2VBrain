"""add library collection status

Revision ID: 0003_add_library_collection_status
Revises: 0002_add_library_metadata
Create Date: 2026-07-10
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_add_library_collection_status"
down_revision: str | None = "0002_add_library_metadata"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "library_items",
        sa.Column(
            "collection_status",
            sa.String(length=32),
            nullable=False,
            server_default="inbox",
        ),
    )


def downgrade() -> None:
    op.drop_column("library_items", "collection_status")
