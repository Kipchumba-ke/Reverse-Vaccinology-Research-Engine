"""Rule-based screen for N-terminal secretory signal peptides.

This follows the three-region structure described by von Heijne:

* n-region: a short N-terminal stretch with no net negative charge
* h-region: a core of about 8 to 15 hydrophobic residues
* c-region: a polar stretch ending in a cleavage site where the residues at
  positions -3 and -1 are small and uncharged (the "(-3,-1) rule")

It is a transparent heuristic, not a trained model. It cannot tell Sec from
Tat signals, lipoprotein signals or signal anchors, and its cleavage position
is only an estimate. Use SignalP or a similar tool when you need a
dependable prediction; app.integrations.signalp can call SignalP 6.
"""

from app.analysis.hydrophobicity import KYTE_DOOLITTLE_SCALE
from app.utils.validation import validate_protein_sequence


METHOD = "Rule-based von Heijne region screen (heuristic)"

H_REGION_WINDOW = 8
H_REGION_MAX_LENGTH = 15
MIN_H_REGION_HYDROPATHY = 2.0
MAX_C_REGION_HYDROPATHY = 1.5
MIN_CLEAVAGE_POSITION = 15
MAX_CLEAVAGE_POSITION = 35
TYPICAL_SIGNAL_PEPTIDE_LENGTH = 22
LENGTH_PENALTY_PER_RESIDUE = 0.15
MINIMUM_SEQUENCE_LENGTH = 30

# Preference for each residue at the cleavage site (position -1) and at
# position -3. Residues that are absent are not allowed there.
POSITION_MINUS_1_SCORES = {"A": 2.0, "G": 1.5, "S": 1.5, "C": 1.0, "T": 1.0}
POSITION_MINUS_3_SCORES = {
    "A": 2.0, "S": 1.5, "G": 1.5, "V": 1.5,
    "I": 1.0, "L": 1.0, "T": 1.0, "C": 1.0,
}


def _mean_hydropathy(residues: str) -> float:
    return sum(KYTE_DOOLITTLE_SCALE[residue] for residue in residues) / len(
        residues
    )


def _find_h_region(sequence: str) -> tuple[int, int, float]:
    """Return the (start, end, mean hydropathy) of the best h-region.

    Positions are 1-based and inclusive. The core is the most hydrophobic
    8-residue window starting at residue 2 to 22; it is then extended to the
    right while residues stay hydrophobic.
    """
    best_start = None
    best_mean = None

    for start in range(2, 23):
        end = start + H_REGION_WINDOW - 1

        if end > len(sequence):
            break

        mean = _mean_hydropathy(sequence[start - 1:end])

        if best_mean is None or mean > best_mean:
            best_start, best_mean = start, mean

    end = best_start + H_REGION_WINDOW - 1

    while (
        end < len(sequence)
        and end - best_start + 1 < H_REGION_MAX_LENGTH
        and KYTE_DOOLITTLE_SCALE[sequence[end]] >= 1.0
    ):
        end += 1

    return best_start, end, best_mean


def _not_detected(reasons: list[str]) -> dict:
    return {
        "detected": False,
        "method": METHOD,
        "confidence": None,
        "cleavage_after": None,
        "reasons": reasons,
    }


def predict_signal_peptide(sequence: str) -> dict:
    """Screen a protein's N-terminus for a classical signal peptide."""
    sequence = validate_protein_sequence(sequence)

    if len(sequence) < MINIMUM_SEQUENCE_LENGTH:
        return _not_detected([
            f"Sequence is shorter than {MINIMUM_SEQUENCE_LENGTH} residues."
        ])

    h_start, h_end, h_mean = _find_h_region(sequence)

    reasons = []

    if h_mean < MIN_H_REGION_HYDROPATHY:
        reasons.append(
            "No sufficiently hydrophobic N-terminal core "
            f"(best mean hydropathy {h_mean:.2f}, "
            f"needs {MIN_H_REGION_HYDROPATHY})."
        )

    n_region = sequence[:h_start - 1]
    n_charge = (
        sum(residue in "KR" for residue in n_region)
        - sum(residue in "DE" for residue in n_region)
    )

    if n_charge < 0:
        reasons.append(
            "The region before the hydrophobic core has a net negative "
            f"charge ({n_charge:+d}), which is atypical for signal peptides."
        )

    best = None

    for position in range(
        max(MIN_CLEAVAGE_POSITION, h_end + 3),
        min(MAX_CLEAVAGE_POSITION, len(sequence) - 1, h_end + 8) + 1,
    ):
        minus_1 = POSITION_MINUS_1_SCORES.get(sequence[position - 1])
        minus_3 = POSITION_MINUS_3_SCORES.get(sequence[position - 3])

        if minus_1 is None or minus_3 is None:
            continue

        c_region = sequence[h_end:position]

        if _mean_hydropathy(c_region) > MAX_C_REGION_HYDROPATHY:
            continue

        score = (
            minus_1
            + minus_3
            - LENGTH_PENALTY_PER_RESIDUE
            * abs(position - TYPICAL_SIGNAL_PEPTIDE_LENGTH)
        )

        if best is None or score > best[0]:
            best = (score, position, c_region)

    if best is None:
        reasons.append(
            "No cleavage site with small residues at positions -3 and -1 "
            "and a polar c-region was found."
        )

    if reasons:
        return _not_detected(reasons)

    score, cleavage_after, c_region = best

    confidence = (
        "medium"
        if h_mean >= 2.5 and n_charge >= 1 and score >= 3.0
        else "low"
    )

    return {
        "detected": True,
        "method": METHOD,
        "confidence": confidence,
        "cleavage_after": cleavage_after,
        "length": cleavage_after,
        "cleavage_motif": sequence[cleavage_after - 3:cleavage_after],
        "n_region": {
            "start": 1,
            "end": h_start - 1,
            "net_charge": n_charge,
        },
        "h_region": {
            "start": h_start,
            "end": h_end,
            "mean_hydropathy": round(h_mean, 3),
        },
        "c_region": {
            "start": h_end + 1,
            "end": cleavage_after,
            "mean_hydropathy": round(_mean_hydropathy(c_region), 3),
        },
        "notes": [
            "The cleavage position is an estimate; confirm with a "
            "trained predictor such as SignalP.",
        ],
    }
