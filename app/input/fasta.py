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

    sequence_id = lines[0][1:].strip()
    sequence = "".join(lines[1:])
    if not sequence:
        raise ValueError("FASTA sequence cannot be empty.")

    sequence = validate_protein_sequence(sequence)

    return {
        "id": sequence_id,
        "sequence": sequence,
    }
