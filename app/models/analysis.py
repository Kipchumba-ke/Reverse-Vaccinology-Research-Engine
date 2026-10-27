from dataclasses import dataclass,field
from datetime import datetime
from uuid import UUID, uuid4


@dataclass
class Analysis:
    id: UUID = field(default_factory=uuid4)
    user_id: UUID | None = None
    protein_id: str | None = None
    protein_name: str | None = None
    organism: str | None = None
    accession: str | None = None
    sequence: str = ""
    status: str = "pending"
    report: dict | None = None
    created_at: datetime | None = None
    epath_gene_id: str | None = None
    epath_ko_id: str | None = None
    host_reference: str | None = None