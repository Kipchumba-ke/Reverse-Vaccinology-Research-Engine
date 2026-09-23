from pathlib import Path

from app.analysis.pipeline import analyze_protein
from app.utils.validation import validate_protein_sequence

def load_fasta_file(path: str | Path) -> dict:
    fasta_text = Path(path).read_text()
    return parse_fasta(fasta_text)

def analyze_fasta_file(path: str | Path):
    record = load_fasta_file(path)

    return analyze_protein(
        record["sequence"],
        protein_id=record["id"],
    )


def _extract_organism(description: str) -> str | None:
    marker = "OS="

    if marker not in description:
        return None

    organism = description.split(marker, 1)[1].strip()

    return organism or None


def _extract_accession(sequence_id: str) -> str | None:
    parts = sequence_id.split("|")

    if len(parts) == 3 and parts[0] == "sp":
        return parts[1]

    return None

def parse_fasta(fasta_text: str) -> dict:
    lines = [
        line.strip()
        for line in fasta_text.splitlines()
        if line.strip()
    ]

    if not lines or not lines[0].startswith(">"):
        raise ValueError("Invalid FASTA input.")

    if any(line.startswith(">") for line in lines[1:]):
        raise ValueError(
            "Multiple FASTA records are not supported."
        )

    records = parse_fasta_records(fasta_text)

    return records[0]


def parse_fasta_records(fasta_text: str) -> list[dict]:
    lines = [
        line.strip()
        for line in fasta_text.splitlines()
        if line.strip()
    ]

    if not lines or not lines[0].startswith(">"):
        raise ValueError("Invalid FASTA input.")

    records = []
    current_id = None
    current_description = ""
    current_sequence = []

    for line in lines:
        if line.startswith(">"):
            if current_id is not None:
                records.append(
                    _build_fasta_record(
                        current_id,
                        current_sequence,
                        current_description,
                    )
                )

            header = line[1:].strip()
            if not header:
                raise ValueError(
                    "FASTA identifier cannot be empty."
                )
            parts = header.split(maxsplit=1)

            current_id = parts[0]
            current_description = parts[1] if len(parts) > 1 else ""

            if not current_id:
                raise ValueError(
                    "FASTA identifier cannot be empty."
                )

            current_sequence = []
        else:
            if current_id is None:
                raise ValueError("Invalid FASTA input.")

            current_sequence.append(line)

    if current_id is None:
        raise ValueError("Invalid FASTA input.")

    records.append(
        _build_fasta_record(
            current_id,
            current_sequence,
            current_description,
        )
    )

    return records


def _build_fasta_record(
    sequence_id: str,
    sequence_parts: list[str],
    description: str = "",
) -> dict:
    if not sequence_parts:
        raise ValueError("FASTA sequence cannot be empty.")

    sequence = validate_protein_sequence(
        "".join(sequence_parts)
    )

    return {
        "id": sequence_id,
        "description": description,
        "organism": _extract_organism(description),
        "accession": _extract_accession(sequence_id),
        "sequence": sequence,
    }
