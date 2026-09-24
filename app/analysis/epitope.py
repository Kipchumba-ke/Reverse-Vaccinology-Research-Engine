from app.analysis.hydrophobicity import calculate_gravy
from app.analysis.properties import calculate_net_charge


def calculate_peptide_properties(
    sequence: str,
    ph: float,
) -> dict:
    if not sequence:
        raise ValueError("Peptide sequence cannot be empty.")

    return {
        "sequence": sequence,
        "length": len(sequence),
        "gravy": calculate_gravy(sequence),
        "net_charge": calculate_net_charge(sequence, ph),
    }

def generate_peptide_windows(
    sequence: str,
    window_size: int,
) -> list[dict]:
    if not sequence:
        raise ValueError("Sequence cannot be empty.")

    if window_size <= 0:
        raise ValueError(
            "Window size must be greater than zero."
        )

    if window_size > len(sequence):
        raise ValueError(
            "Window size cannot exceed sequence length."
        )

    return [
        {
            "start": start,
            "end": start + window_size - 1,
            "sequence": sequence[start - 1:start - 1 + window_size],
        }
        for start in range(
            1,
            len(sequence) - window_size + 2,
        )
    ]

def annotate_transmembrane_overlap(
    peptides: list[dict],
    transmembrane_regions: list[dict],
) -> list[dict]:
    annotated = []

    for peptide in peptides:
        peptide_start = peptide["start"]
        peptide_end = peptide["end"]

        overlaps = any(
            peptide_start <= region["end"]
            and peptide_end >= region["start"]
            for region in transmembrane_regions
        )

        annotated.append({
            **peptide,
            "overlaps_transmembrane": overlaps,
        })

    return annotated

def annotate_conservation_overlap(
    peptides: list[dict],
    conserved_regions: list[dict],
) -> list[dict]:
    annotated = []

    for peptide in peptides:
        peptide_start = peptide["start"]
        peptide_end = peptide["end"]

        overlaps = any(
            peptide_start <= region["end"]
            and peptide_end >= region["start"]
            for region in conserved_regions
        )

        annotated.append({
            **peptide,
            "overlaps_conserved_region": overlaps,
        })

    return annotated

