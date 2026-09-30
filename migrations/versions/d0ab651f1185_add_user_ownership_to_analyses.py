"""Add user ownership to analyses

Revision ID: d0ab651f1185
Revises: b14488cff728
Create Date: 2026-09-30 13:43:40.780290

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'd0ab651f1185'
down_revision: Union[str, Sequence[str], None] = 'b14488cff728'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column(
        "analyses",
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )


def downgrade():
    op.drop_column("analyses", "user_id")
