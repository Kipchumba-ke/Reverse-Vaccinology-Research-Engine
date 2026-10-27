"""Add host reference selection to analyses."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "7c2f4a9d81b6"
down_revision: Union[str, Sequence[str], None] = "fe4ba94b2fec"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "analyses",
        sa.Column(
            "host_reference",
            sa.String(length=20),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("analyses", "host_reference")