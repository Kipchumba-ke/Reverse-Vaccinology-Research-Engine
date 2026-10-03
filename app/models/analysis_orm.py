import uuid
from uuid import UUID

from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy import JSON ,String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AnalysisModel(Base):
    __tablename__ = "analyses"

    id: Mapped[uuid.UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[UUID | None] = mapped_column(
        nullable=True,
    )
    protein_id: Mapped[str | None] = mapped_column(String(255))
    protein_name: Mapped[str | None] = mapped_column(String(255))
    organism: Mapped[str | None] = mapped_column(String(255))
    accession: Mapped[str | None] = mapped_column(String(100))
    sequence: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending",
    )
    report: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    def __init__(self, **kwargs):
        kwargs.setdefault("id", uuid.uuid4())
        kwargs.setdefault("status", "pending")
        super().__init__(**kwargs)