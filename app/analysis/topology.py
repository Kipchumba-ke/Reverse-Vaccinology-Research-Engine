"""Combine signal-peptide and transmembrane screens into topology hints.

The hydropathy-based transmembrane screen cannot tell a signal peptide's
hydrophobic core from a membrane-spanning helix. These helpers reconcile the
two screens and derive a coarse, low-confidence localization hint.

The hint is NOT localization evidence. It is derived from the same sequence
heuristics and is deliberately kept apart from evidence supplied by UniProt,
NCBI, PSORTb or experiments.
"""

SIGNAL_PEPTIDE_H_REGION = "signal_peptide_h_region"

HINT_SOURCE = "ReverseVax topology heuristic"


def _overlaps_signal_peptide(candidate: dict, signal_peptide: dict) -> bool:
    if not signal_peptide.get("detected"):
        return False

    return candidate["start"] <= signal_peptide["cleavage_after"]


def flag_signal_peptide_overlap(
    candidates: list[dict],
    signal_peptide: dict,
) -> list[dict]:
    """Mark hydrophobic regions that fall inside a predicted signal peptide.

    The original classification is kept. Each region gains
    overlaps_signal_peptide and revised_classification, which is
    "signal_peptide_h_region" for regions overlapping the signal peptide.
    """
    flagged = []

    for candidate in candidates:
        overlaps = _overlaps_signal_peptide(candidate, signal_peptide)

        flagged.append({
            **candidate,
            "overlaps_signal_peptide": overlaps,
            "revised_classification": (
                SIGNAL_PEPTIDE_H_REGION
                if overlaps
                else candidate.get("classification")
            ),
        })

    return flagged


def count_transmembrane_segments(candidates: list[dict]) -> int:
    """Count regions that remain transmembrane candidates after revision."""
    return sum(
        1
        for candidate in candidates
        if candidate.get("revised_classification",
                         candidate.get("classification"))
        == "candidate_transmembrane"
    )


def infer_localization_hint(
    signal_peptide: dict,
    candidates: list[dict],
) -> dict:
    """Give a coarse localization hint from topology features."""
    segments = count_transmembrane_segments(candidates)
    has_signal_peptide = bool(signal_peptide.get("detected"))

    if segments >= 1:
        hint = "membrane_associated"
        basis = [
            f"{segments} candidate transmembrane segment(s) outside any "
            "predicted signal peptide."
        ]
        if has_signal_peptide:
            basis.append("A signal peptide was also predicted.")
    elif has_signal_peptide:
        hint = "secreted_or_periplasmic"
        basis = [
            "A signal peptide was predicted and no transmembrane segment "
            "was found."
        ]
    else:
        hint = "cytoplasmic_or_unclassified"
        basis = [
            "No signal peptide and no transmembrane segment were found."
        ]

    caveats = [
        "Derived from sequence heuristics only; not independent "
        "localization evidence.",
    ]

    if hint == "cytoplasmic_or_unclassified":
        caveats.append(
            "Outer-membrane beta-barrel proteins, lipoproteins and "
            "proteins secreted without a classical signal peptide are "
            "missed by this screen."
        )

    return {
        "hint": hint,
        "confidence": "low",
        "source": HINT_SOURCE,
        "basis": basis,
        "caveats": caveats,
    }
