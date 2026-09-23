from dataclasses import dataclass,field
from uuid import UUID, uuid4


@dataclass
class Analysis:
    id: UUID = field(default_factory=uuid4)
    protein_id: str | None = None
    protein_name: str | None = None
    organism: str | None = None
    accession: str | None = None
    sequence: str = ""
    status: str = "pending"