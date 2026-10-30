"""Optional PSORTb 3.0 integration (local command line or Docker).

PSORTb has no public REST API. Install it yourself, for example with the
``brinkmanlab/psortb_commandline`` Docker image, and point this adapter at
a wrapper or the ``psort`` executable. Off by default:

    PSORTB_ENABLED=1
    PSORTB_EXECUTABLE=/path/to/psort      (optional if on PATH)
    PSORTB_GRAM=negative                  (negative, positive or archaea)

The terse output layout (``SeqID<TAB>Localization<TAB>Score``) was checked
against an open-source wrapper's test data, but this adapter has not been
run against a live PSORTb install. Run one real protein through it first.

PSORTb scores run from 0 to 10; 7.5 is its usual confidence cut-off, and
the adapter reports lower scores as low confidence.
"""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from app.analysis.localization import create_localization_evidence

SOURCE = "PSORTb 3.0"
VALID_GRAM = {"negative": "--negative", "positive": "--positive",
              "archaea": "--archaea"}
TIMEOUT_SECONDS = 600
CONFIDENT_SCORE = 7.5

LOCATION_MAP = {
    "Cytoplasmic": "cytoplasm",
    "CytoplasmicMembrane": "inner_membrane",
    "Periplasmic": "periplasm",
    "OuterMembrane": "outer_membrane",
    "Extracellular": "extracellular",
    "Cellwall": "extracellular",
    "Unknown": "unknown",
}


def is_psortb_enabled() -> bool:
    return os.environ.get("PSORTB_ENABLED", "").strip().lower() in {
        "1", "true", "yes", "on",
    }


def parse_terse_output(text: str) -> dict:
    """Parse ``--output terse`` output for a single sequence."""
    rows = [
        line.split("\t")
        for line in text.splitlines()
        if line.strip()
    ]

    if rows and rows[0][0].strip() == "SeqID":
        rows = rows[1:]

    if len(rows) != 1 or len(rows[0]) < 3:
        raise ValueError(
            "Expected one SeqID/Localization/Score row in PSORTb output."
        )

    _, localization, score = (field.strip() for field in rows[0][:3])

    if localization not in LOCATION_MAP:
        raise ValueError(f"Unrecognised PSORTb localization: {localization}")

    return {
        "method": SOURCE,
        "localization": localization,
        "location": LOCATION_MAP[localization],
        "score": float(score),
    }


def to_localization_evidence(prediction: dict, gram: str) -> list:
    score = prediction["score"]
    confident = score >= CONFIDENT_SCORE

    if prediction["location"] == "unknown":
        description = (
            "PSORTb could not assign a localization (it returned "
            "Unknown)."
        )
    else:
        description = (
            f"PSORTb ({gram} mode) predicts {prediction['localization']} "
            f"with score {score:g} of 10"
            + ("." if confident else f", below its {CONFIDENT_SCORE:g} "
               "confidence cut-off.")
        )

    return [create_localization_evidence(
        location=prediction["location"],
        source=SOURCE,
        confidence="medium" if confident else "low",
        description=description,
    )]


def run_psortb(sequence: str, gram: str | None = None) -> dict:
    gram = (gram or os.environ.get("PSORTB_GRAM", "negative")).lower()

    if gram not in VALID_GRAM:
        raise ValueError(
            "PSORTB_GRAM must be one of: " + ", ".join(sorted(VALID_GRAM))
        )

    executable = os.environ.get("PSORTB_EXECUTABLE") or shutil.which("psort")

    if not executable:
        raise RuntimeError("psort executable not found.")

    with tempfile.TemporaryDirectory(prefix="psortb-") as workdir:
        fasta = Path(workdir) / "query.fasta"
        results = Path(workdir) / "results"
        results.mkdir()
        fasta.write_text(f">query\n{sequence}\n")

        try:
            completed = subprocess.run(
                [executable, VALID_GRAM[gram], "-o", "terse",
                 "-r", str(results), "-i", str(fasta)],
                text=True,
                capture_output=True,
                check=True,
                timeout=TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired as error:
            raise RuntimeError("PSORTb timed out.") from error
        except subprocess.CalledProcessError as error:
            message = (error.stderr or "").strip()
            raise RuntimeError(
                f"PSORTb execution failed: {message}"
                if message else "PSORTb execution failed."
            ) from error

        # PSORTb writes its report into the results directory; fall back to
        # standard output for wrappers that print it instead.
        report_files = sorted(results.glob("*terse*")) or sorted(
            results.glob("*.txt")
        )
        output = (
            report_files[0].read_text() if report_files else completed.stdout
        )

    prediction = parse_terse_output(output)
    prediction["gram"] = gram
    return prediction


def fetch_psortb_prediction(sequence: str) -> dict:
    """Run PSORTb; report failures instead of raising."""
    try:
        return {"status": "completed", **run_psortb(sequence)}
    except (RuntimeError, ValueError, OSError) as error:
        return {
            "status": "lookup_failed",
            "method": SOURCE,
            "message": str(error) or "PSORTb failed.",
        }
