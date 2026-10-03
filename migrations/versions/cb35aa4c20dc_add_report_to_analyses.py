"""add report to analyses

Revision ID: cb35aa4c20dc
Revises: d0ab651f1185
Create Date: 2026-10-03 14:31:28.259516

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cb35aa4c20dc'
down_revision: Union[str, Sequence[str], None] = 'd0ab651f1185'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column(
        "analyses",
        sa.Column(
            "report",
            sa.JSON(),
            nullable=True,
        ),
    )


def downgrade():
    op.drop_column("analyses", "report")
