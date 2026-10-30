"""Sequence-based screen for candidate B-cell antigenic regions.

Implements the Kolaskar and Tongaonkar (1990, FEBS Letters 276:172-174)
antigenic propensity method. Each amino acid has a propensity to occur in
known antigenic determinants. The propensity is averaged over a sliding
window; stretches of at least eight residues that score above the protein's
own average are reported as candidate antigenic determinants.

This is an old, scale-based method. The authors reported about 75 percent
accuracy on their test set, and it says nothing about surface exposure,
3D structure, T-cell epitopes or whether an antibody would really bind.
Treat the output as a way to shortlist regions for further tools (for
example BepiPred through app.integrations.iedb) and for experiments.
"""

from app.utils.validation import validate_protein_sequence


METHOD = "Kolaskar-Tongaonkar antigenic propensity (1990)"

PROPENSITY = {
    "A": 1.064, "R": 0.874, "N": 0.776, "D": 0.866, "C": 1.412,
    "Q": 1.015, "E": 0.851, "G": 0.874, "H": 1.105, "I": 1.152,
    "L": 1.250, "K": 0.930, "M": 0.826, "F": 1.091, "P": 1.064,
    "S": 1.012, "T": 0.909, "W": 0.893, "Y": 1.161, "V": 1.383,
}

DEFAULT_WINDOW = 7
DEFAULT_MIN_REGION_LENGTH = 8
_EPSILON = 1e-9


def calculate_propensity_profile(
    sequence: str,
    window: int = DEFAULT_WINDOW,
) -> list[float | None]:
    """Return the windowed propensity for every residue.

    The score of a window is assigned to its central residue. Residues
    within window // 2 of either end have no score (None).
    """
    sequence = validate_protein_sequence(sequence)

    if window <= 0 or window % 2 == 0:
        raise ValueError("Window size must be a positive odd number.")

    half = window // 2
    profile = [None] * len(sequence)

    if len(sequence) < window:
        return profile

    for center in range(half, len(sequence) - half):
        segment = sequence[center - half:center + half + 1]
        profile[center] = sum(PROPENSITY[residue] for residue in segment) / window

    return profile


def predict_antigenic_regions(
    sequence: str,
    window: int = DEFAULT_WINDOW,
    min_region_length: int = DEFAULT_MIN_REGION_LENGTH,
) -> dict:
    """Find candidate antigenic determinants in a protein sequence.

    Region coordinates are 1-based and inclusive. As in the original
    method, a region is a run of window-centre positions whose windowed
    propensity is at or above the threshold.
    """
    sequence = validate_protein_sequence(sequence)

    if min_region_length <= 0:
        raise ValueError("Minimum region length must be greater than zero.")

    profile = calculate_propensity_profile(sequence, window=window)
    threshold = sum(PROPENSITY[residue] for residue in sequence) / len(sequence)

    result = {
        "method": METHOD,
        "window": window,
        "min_region_length": min_region_length,
        "threshold": round(threshold, 4),
        "threshold_basis": "average propensity of this protein",
        "regions": [],
        "notes": [
            "Scale-based screen; it does not model structure, surface "
            "exposure or T-cell epitopes.",
        ],
    }

    if len(sequence) < window:
        result["notes"].append(
            f"Sequence is shorter than the {window}-residue window."
        )
        return result

    run_start = None

    for index, score in enumerate(profile + [None]):
        above = score is not None and score >= threshold - _EPSILON

        if above and run_start is None:
            run_start = index

        if not above and run_start is not None:
            length = index - run_start

            if length >= min_region_length:
                scores = profile[run_start:index]
                result["regions"].append({
                    "start": run_start + 1,
                    "end": index,
                    "length": length,
                    "sequence": sequence[run_start:index],
                    "mean_propensity": round(sum(scores) / length, 4),
                })

            run_start = None

    return result


def annotate_peptides_with_antigenicity(
    peptides: list[dict],
    antigenic_regions: list[dict],
) -> list[dict]:
    """Add antigenic-region overlap and mean propensity to peptide windows."""
    annotated = []

    for peptide in peptides:
        residues = peptide["sequence"]

        annotated.append({
            **peptide,
            "mean_antigenic_propensity": round(
                sum(PROPENSITY[residue] for residue in residues)
                / len(residues),
                4,
            ),
            "overlaps_antigenic_region": any(
                peptide["start"] <= region["end"]
                and peptide["end"] >= region["start"]
                for region in antigenic_regions
            ),
        })

    return annotated
