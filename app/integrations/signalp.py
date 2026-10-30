"""Optional SignalP 6.0 integration (local command-line install).

Off by default. Enable it by installing SignalP 6.0 on the machine that
runs the analysis and setting:

    SIGNALP_ENABLED=1
    SIGNALP6_EXECUTABLE=/path/to/signalp6     (optional if on PATH)
    SIGNALP_ORGANISM=other                    (other or eukarya; default
                                               other, which covers
                                               bacteria)

SignalP is licensed separately by DTU and is not bundled or redistributed
with this project. This adapter has been tested against a hand-written
sample of the prediction_results.txt layout, not against a live SignalP
installation, so run one real protein through it before relying on it.

A signal peptide says a protein enters the secretory pathway. It does not
say which compartment the protein ends up in, so the result is stored as a
sequence prediction and is not turned into localization evidence.
"""

import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

SOURCE = "SignalP 6.0"
VALID_ORGANISMS = {"other", "eukarya"}
TIMEOUT_SECONDS = 300

# Prediction labels in the SignalP 6.0 summary table.
SIGNAL_PEPTIDE_TYPES = {
    "SP": "Sec/SPI (standard secretory signal peptide)",
    "LIPO": "Sec/SPII (lipoprotein signal peptide)",
    "TAT": "Tat/SPI (twin-arginine signal peptide)",
    "TATLIPO": "Tat/SPII (twin-arginine lipoprotein signal peptide)",
    "PILIN": "Sec/SPIII (pilin-like signal peptide)",
}

_CLEAVAGE = re.compile(r"CS pos:\s*(\d+)-(\d+)")
_PROBABILITY = re.compile(r"Pr:\s*([0-9.]+)")


def is_signalp_enabled() -> bool:
    return os.environ.get("SIGNALP_ENABLED", "").strip().lower() in {
        "1", "true", "yes", "on",
    }


def _resolve_executable() -> str:
    executable = (
        os.environ.get("SIGNALP6_EXECUTABLE") or shutil.which("signalp6")
    )

    if not executable:
        raise RuntimeError("signalp6 executable not found.")

    return executable


def parse_signalp_prediction(text: str) -> dict:
    """Parse prediction_results.txt for a single sequence."""
    rows = [
        line.split("\t")
        for line in text.splitlines()
        if line.strip() and not line.startswith("#")
    ]

    if len(rows) != 1:
        raise ValueError(
            "Expected exactly one prediction row in SignalP output."
        )

    fields = rows[0]

    if len(fields) < 3:
        raise ValueError("SignalP output row is incomplete.")

    label = fields[1].strip()
    cleavage_field = fields[-1] if len(fields) > 8 else ""
    cleavage = _CLEAVAGE.search(cleavage_field)
    probability = _PROBABILITY.search(cleavage_field)

    if label == "OTHER":
        return {
            "detected": False,
            "method": SOURCE,
            "prediction": "OTHER",
            "notes": ["SignalP predicts no signal peptide."],
        }

    if label not in SIGNAL_PEPTIDE_TYPES:
        raise ValueError(f"Unrecognised SignalP prediction: {label}")

    return {
        "detected": True,
        "method": SOURCE,
        "prediction": label,
        "signal_peptide_type": SIGNAL_PEPTIDE_TYPES[label],
        "cleavage_after": int(cleavage.group(1)) if cleavage else None,
        "cleavage_probability": (
            float(probability.group(1)) if probability else None
        ),
        "notes": [],
    }


def run_signalp(sequence: str, organism: str | None = None) -> dict:
    """Run SignalP 6.0 on one sequence and return the parsed prediction."""
    organism = organism or os.environ.get("SIGNALP_ORGANISM", "other")

    if organism not in VALID_ORGANISMS:
        raise ValueError(
            "SIGNALP_ORGANISM must be one of: "
            + ", ".join(sorted(VALID_ORGANISMS))
        )

    executable = _resolve_executable()

    with tempfile.TemporaryDirectory(prefix="signalp-") as workdir:
        fasta = Path(workdir) / "query.fasta"
        output_dir = Path(workdir) / "out"
        fasta.write_text(f">query\n{sequence}\n")

        try:
            subprocess.run(
                [
                    executable,
                    "--fastafile", str(fasta),
                    "--output_dir", str(output_dir),
                    "--organism", organism,
                    "--format", "none",
                    "--mode", "fast",
                ],
                text=True,
                capture_output=True,
                check=True,
                timeout=TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError("SignalP timed out.") from exc
        except subprocess.CalledProcessError as exc:
            message = (exc.stderr or "").strip()
            raise RuntimeError(
                f"SignalP execution failed: {message}"
                if message
                else "SignalP execution failed."
            ) from exc

        results = output_dir / "prediction_results.txt"

        if not results.is_file():
            raise RuntimeError("SignalP produced no prediction_results.txt.")

        return parse_signalp_prediction(results.read_text())


def fetch_signalp_prediction(sequence: str) -> dict:
    """Run SignalP when enabled; report failures instead of raising."""
    try:
        return {"status": "completed", **run_signalp(sequence)}
    except (RuntimeError, ValueError, OSError) as error:
        return {
            "status": "lookup_failed",
            "detected": None,
            "method": SOURCE,
            "message": str(error) or "SignalP failed.",
        }
