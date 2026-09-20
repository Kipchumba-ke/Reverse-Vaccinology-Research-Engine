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
    current_sequence = []

    for line in lines:
        if line.startswith(">"):
            if current_id is not None:
                records.append(
                    _build_fasta_record(
                        current_id,
                        current_sequence,
                    )
                )

            current_id = line[1:].strip()

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
        )
    )

    return records


def _build_fasta_record(
    sequence_id: str,
    sequence_parts: list[str],
) -> dict:
    if not sequence_parts:
        raise ValueError("FASTA sequence cannot be empty.")

    sequence = validate_protein_sequence(
        "".join(sequence_parts)
    )

    return {
        "id": sequence_id,
        "sequence": sequence,
    }
