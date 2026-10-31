"""Optional DeepTMHMM integration through DTU's BioLib cloud service.

DeepTMHMM has no plain REST endpoint. DTU publishes it as the BioLib app
``DTU/DeepTMHMM``, run from Python with the ``pybiolib`` package:

    pip install pybiolib

Off by default. Enable it with:

    DEEPTMHMM_ENABLED=1
    BIOLIB_TOKEN=...      (required on a server; create it in your BioLib
                           account settings, or run ``biolib login`` once on
                           a workstation)

Your sequence is sent to BioLib's servers, so do not enable it for
unpublished or confidential sequences. Use is subject to the BioLib and DTU
terms. The adapter is tested on a hand-written sample of the ``.3line``
layout, not against the live service, so run one real protein through it
before relying on it.

DeepTMHMM labels each residue. This adapter reads the label string:
S signal peptide, M alpha-helical transmembrane, B beta strand (outer
membrane barrel), I inside, O outside, P periplasmic.
Whole-protein classes are SP, TM, SP+TM, GLOBULAR and BETA. Only TM, SP+TM
and BETA say anything about a compartment; SP and GLOBULAR do not, so they
produce no localization evidence.
"""

import os
import re

from app.analysis.localization import create_localization_evidence
from app.integrations.common import NotConfigured, run_biolib_app

SOURCE = "DeepTMHMM"
APP_NAME = "DTU/DeepTMHMM"
VALID_CLASSES = {"SP", "TM", "SP+TM", "GLOBULAR", "BETA"}

# Spellings seen in the service's output, mapped to the class stored here.
_CLASS_ALIASES = {"GLOB": "GLOBULAR"}

_SEGMENT_TYPES = {
    "S": "signal_peptide",
    "M": "transmembrane_helix",
    "B": "beta_strand",
}


def is_deeptmhmm_enabled() -> bool:
    return os.environ.get("DEEPTMHMM_ENABLED", "").strip().lower() in {
        "1", "true", "yes", "on",
    }


def parse_label_segments(labels: str) -> list[dict]:
    """Collapse a per-residue label string into 1-based segments."""
    segments = []

    for match in re.finditer(r"([SMB])\1*", labels):
        segments.append({
            "type": _SEGMENT_TYPES[match.group(1)],
            "start": match.start() + 1,
            "end": match.end(),
        })

    return segments


def parse_three_line(text: str) -> dict:
    """Parse predicted_topologies.3line for a single sequence."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    if len(lines) != 3 or not lines[0].startswith(">"):
        raise ValueError(
            "Expected one header, one sequence and one label line in "
            "DeepTMHMM output."
        )

    header, sequence, labels = lines

    if len(sequence) != len(labels):
        raise ValueError(
            "DeepTMHMM sequence and label lines differ in length."
        )

    predicted_class = header.rsplit("|", 1)[-1].strip()
    predicted_class = _CLASS_ALIASES.get(predicted_class, predicted_class)

    if predicted_class not in VALID_CLASSES:
        raise ValueError(
            f"Unrecognised DeepTMHMM class: {predicted_class!r}"
        )

    segments = parse_label_segments(labels)

    return {
        "method": SOURCE,
        "predicted_class": predicted_class,
        "segments": segments,
        "transmembrane_helices": sum(
            1 for s in segments if s["type"] == "transmembrane_helix"
        ),
        "beta_strands": sum(
            1 for s in segments if s["type"] == "beta_strand"
        ),
        "topology": labels,
    }


def to_localization_evidence(prediction: dict) -> list:
    """Turn a prediction into localization evidence where it supports one.

    The compartments assume a Gram-negative bacterium: an alpha-helical
    membrane protein is placed in the inner membrane and a beta-barrel in
    the outer membrane. Gram-positive bacteria have no outer membrane.
    """
    predicted_class = prediction["predicted_class"]

    if predicted_class in {"TM", "SP+TM"}:
        count = prediction["transmembrane_helices"]
        return [create_localization_evidence(
            location="inner_membrane",
            source=SOURCE,
            confidence="medium",
            description=(
                f"DeepTMHMM predicts {count} alpha-helical transmembrane "
                "segment(s). Placed in the inner membrane assuming a "
                "Gram-negative bacterium."
            ),
        )]

    if predicted_class == "BETA":
        return [create_localization_evidence(
            location="outer_membrane",
            source=SOURCE,
            confidence="medium",
            description=(
                "DeepTMHMM predicts a beta-barrel transmembrane protein. "
                "Placed in the outer membrane assuming a Gram-negative "
                "bacterium."
            ),
        )]

    return []


def run_deeptmhmm(sequence: str) -> dict:
    """Run DeepTMHMM on BioLib for one sequence."""
    text = run_biolib_app(
        APP_NAME,
        "--fasta input.fasta",
        f">query\n{sequence}\n",
        "*.3line",
        SOURCE,
    )

    return parse_three_line(text)


def fetch_deeptmhmm_prediction(sequence: str) -> dict:
    """Run DeepTMHMM; report failures instead of raising."""
    try:
        prediction = run_deeptmhmm(sequence)
    except NotConfigured as error:
        return {
            "status": "not_configured",
            "method": SOURCE,
            "message": str(error),
        }
    except (RuntimeError, ValueError, OSError) as error:
        return {
            "status": "lookup_failed",
            "method": SOURCE,
            "message": str(error) or "DeepTMHMM failed.",
        }

    return {"status": "completed", **prediction}
