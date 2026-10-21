"""add created_at to analyses

Revision ID: dd1c2e92095e
Revises: cb35aa4c20dc
Create Date: 2026-10-19 21:42:11.532416

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dd1c2e92095e'
down_revision: Union[str, Sequence[str], None] = 'cb35aa4c20dc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "analyses",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )


def downgrade() -> None:
    op.drop_column("analyses", "created_at")
