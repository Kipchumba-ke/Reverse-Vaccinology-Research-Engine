from dataclasses import dataclass, field
from uuid import UUID, uuid4


@dataclass
class User:
    id: UUID = field(default_factory=uuid4)
    email: str = ""
    password_hash: str = ""