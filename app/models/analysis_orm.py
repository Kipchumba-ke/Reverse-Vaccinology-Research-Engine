import uuid

from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AnalysisModel(Base):
    __tablename__ = "analyses"

    id: Mapped[uuid.UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        primary_key=True
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