"""Optional SignalP 6.0 integration.

Off by default. Two backends; pick one with SIGNALP_BACKEND.

Local install (default), no data leaves the machine:

    SIGNALP_ENABLED=1
    SIGNALP_BACKEND=local
    SIGNALP6_EXECUTABLE=/path/to/signalp6     (optional if on PATH)

BioLib cloud, no local licence or model weights, run with ``pybiolib``:

    pip install pybiolib
    SIGNALP_ENABLED=1
    SIGNALP_BACKEND=biolib
    SIGNALP_BIOLIB_APP=DTU/SignalP_6          (optional; this is the default)
    BIOLIB_TOKEN=...                          (required on a server)

Shared setting:

    SIGNALP_ORGANISM=other                    (other or eukarya; default
                                               other, which covers
                                               bacteria)

The BioLib backend sends your sequence to BioLib's servers, so do not use it
for unpublished or confidential sequences. Use is subject to the BioLib and
DTU terms. SignalP is licensed separately by DTU and is not bundled or
redistributed with this project.

Both backends read the same ``prediction_results.txt``. The parser is tested
against a hand-written sample of that layout, and the BioLib app name and
arguments come from a third-party code sample, not from a run of this
project, so run one real protein through the adapter before relying on it.

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

from app.integrations.common import NotConfigured, run_biolib_app

SOURCE = "SignalP 6.0"
VALID_ORGANISMS = {"other", "eukarya"}
VALID_BACKENDS = {"local", "biolib"}
DEFAULT_BIOLIB_APP = "DTU/SignalP_6"
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
    configured = os.environ.get("SIGNALP6_EXECUTABLE", "").strip()
    executable = configured or shutil.which("signalp6")

    if not executable or not (
        shutil.which(executable) or os.path.isfile(executable)
    ):
        raise NotConfigured(
            "SignalP is switched on but no signalp6 install was found"
            + (f" at {configured}" if configured else "")
            + ". SignalP 6.0 is licensed by DTU (academic use is free): "
            "install it and set SIGNALP6_EXECUTABLE, set "
            "SIGNALP_BACKEND=biolib to use the BioLib cloud app, or set "
            "SIGNALP_ENABLED=0."
        )

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


def _resolve_backend() -> str:
    backend = os.environ.get("SIGNALP_BACKEND", "local").strip().lower()

    if backend not in VALID_BACKENDS:
        raise ValueError(
            "SIGNALP_BACKEND must be one of: "
            + ", ".join(sorted(VALID_BACKENDS))
        )

    return backend


def _resolve_organism(organism: str | None) -> str:
    organism = organism or os.environ.get("SIGNALP_ORGANISM", "other")

    if organism not in VALID_ORGANISMS:
        raise ValueError(
            "SIGNALP_ORGANISM must be one of: "
            + ", ".join(sorted(VALID_ORGANISMS))
        )

    return organism


def _read_results(output_dir: Path) -> dict:
    matches = sorted(output_dir.rglob("prediction_results.txt"))

    if not matches:
        raise RuntimeError("SignalP produced no prediction_results.txt.")

    return parse_signalp_prediction(matches[0].read_text())


def _run_local(sequence: str, organism: str) -> dict:
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

        return _read_results(output_dir)


def _run_biolib(sequence: str, organism: str) -> dict:
    app_name = os.environ.get("SIGNALP_BIOLIB_APP") or DEFAULT_BIOLIB_APP

    text = run_biolib_app(
        app_name,
        (
            "--fastafile input.fasta "
            f"--organism {organism} "
            "--format txt --mode fast --output_dir output"
        ),
        f">query\n{sequence}\n",
        "prediction_results.txt",
        "SignalP",
    )

    return parse_signalp_prediction(text)


def run_signalp(sequence: str, organism: str | None = None) -> dict:
    """Run SignalP 6.0 on one sequence and return the parsed prediction."""
    organism = _resolve_organism(organism)

    if _resolve_backend() == "biolib":
        return _run_biolib(sequence, organism)

    return _run_local(sequence, organism)


def fetch_signalp_prediction(sequence: str) -> dict:
    """Run SignalP when enabled; report failures instead of raising."""
    try:
        return {"status": "completed", **run_signalp(sequence)}
    except NotConfigured as error:
        return {
            "status": "not_configured",
            "detected": None,
            "method": SOURCE,
            "message": str(error),
        }
    except (RuntimeError, ValueError, OSError) as error:
        return {
            "status": "lookup_failed",
            "detected": None,
            "method": SOURCE,
            "message": str(error) or "SignalP failed.",
        }
