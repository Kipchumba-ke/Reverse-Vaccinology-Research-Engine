from pathlib import Path

from app.analysis.pipeline import analyze_protein
from app.utils.validation import validate_protein_sequence
import re


def _extract_accession(sequence_id: str) -> str | None:
    """Extract accessions from UniProt and common NCBI protein headers."""
    parts = sequence_id.split("|")

    if len(parts) >= 3 and parts[0] in {"sp", "tr"}:
        return parts[1] or None

    # Examples: ALR82097.1, NP_123456.1, WP_012345678.1
    if re.fullmatch(
        r"(?:[A-Z]{3}\d{5,7}|[A-Z]{2}_\d{6,9})(?:\.\d+)?",
        sequence_id,
    ):
        return sequence_id

    return None


def _extract_organism(description: str) -> str | None:
    """Extract organism from UniProt OS= or a bracketed NCBI description."""
    if not description:
        return None

    if "OS=" in description:
        organism = description.split("OS=", 1)[1]
        organism = re.split(
            r"\s+(?:OX|GN|PE|SV)=",
            organism,
            maxsplit=1,
        )[0].strip()

        if organism:
            return organism

    match = re.search(r"\[([^\[\]]+)\]\s*$", description)
    return match.group(1).strip() if match else None

def load_fasta_file(path: str | Path) -> dict:
    fasta_text = Path(path).read_text()
    return parse_fasta(fasta_text)

def analyze_fasta_file(path: str | Path):
    record = load_fasta_file(path)

    return analyze_protein(
        record["sequence"],
        protein_id=record["id"],
    )




def _extract_entry_name(sequence_id: str) -> str | None:
    parts = sequence_id.split("|")

    if (
        len(parts) == 3
        and parts[0] in {"sp", "tr"}
        and parts[2]
    ):
        return parts[2]

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
        "entry_name": _extract_entry_name(sequence_id),
        "description": description,
        "organism": _extract_organism(description),
        "accession": _extract_accession(sequence_id),
        "sequence": sequence,
    }
