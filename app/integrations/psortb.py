"""Optional PSORTb 3.0 integration (Docker image or local install).

PSORTb is open source and has no public REST API, so it runs on your own
machine. Off by default. Two ways to run it, chosen with PSORTB_BACKEND.

Docker (recommended; no academic access needed). Pull the image once:

    docker pull brinkmanlab/psortb_commandline:1.0.2

    PSORTB_ENABLED=1
    PSORTB_BACKEND=docker
    PSORTB_DOCKER_IMAGE=brinkmanlab/psortb_commandline:1.0.2   (default)
    DOCKER_EXECUTABLE=docker                                   (default)
    PSORTB_GRAM=negative                  (negative, positive or archaea)

The adapter starts the container itself with the input and results
directories mounted, so the process that runs the analysis (the API or the
Celery worker) must be able to run ``docker run`` on a Docker daemon that
shares its filesystem. That holds when the worker runs directly on the host.
It does not hold inside the provided worker container unless you mount the
Docker socket and the same temporary path, which also gives that container
control of the host's Docker. For a containerised deployment install PSORTb
into the image instead and use the local backend.

Local install:

    PSORTB_ENABLED=1
    PSORTB_BACKEND=local                  (default)
    PSORTB_EXECUTABLE=/path/to/psort      (optional if on PATH)

The terse output layout (``SeqID<TAB>Localization<TAB>Score``) was checked
against an open-source wrapper's test data, but this adapter has not been
run against a live PSORTb install, and the Docker command line was written
from the image's published wrapper script. Run one real protein through it
first.

PSORTb scores run from 0 to 10; 7.5 is its usual confidence cut-off, and
the adapter reports lower scores as low confidence. PSORTb is made for
bacteria and archaea: it gives no meaningful result for a eukaryotic or
viral protein.
"""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from app.analysis.localization import create_localization_evidence
from app.integrations.common import NotConfigured

SOURCE = "PSORTb 3.0"
VALID_GRAM = {"negative": "--negative", "positive": "--positive",
              "archaea": "--archaea"}
VALID_BACKENDS = {"local", "docker"}
DEFAULT_DOCKER_IMAGE = "brinkmanlab/psortb_commandline:1.0.2"
DOCKER_PSORT_PATH = "/usr/local/psortb/bin/psort"
DOCKER_RESULTS_DIR = "/tmp/results"
DEFAULT_TIMEOUT_SECONDS = 1800
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


def _timeout_seconds() -> int:
    raw = os.environ.get("PSORTB_TIMEOUT_SECONDS", "").strip()

    if not raw:
        return DEFAULT_TIMEOUT_SECONDS

    try:
        value = int(raw)
    except ValueError as error:
        raise ValueError(
            "PSORTB_TIMEOUT_SECONDS must be a whole number of seconds."
        ) from error

    if value <= 0:
        raise ValueError("PSORTB_TIMEOUT_SECONDS must be greater than zero.")

    return value


def is_psortb_enabled() -> bool:
    return os.environ.get("PSORTB_ENABLED", "").strip().lower() in {
        "1", "true", "yes", "on",
    }


def _snippet(text: str, limit: int = 300) -> str:
    shown = text.strip()

    if not shown:
        return "(empty)"

    return repr(shown[:limit] + ("..." if len(shown) > limit else ""))


def _split_row(line: str) -> list[str]:
    if "\t" in line:
        return [field.strip() for field in line.split("\t")]

    return line.split()


def _as_score(value: str) -> float | None:
    try:
        return float(value)
    except ValueError:
        return None


def parse_terse_output(text: str) -> dict:
    """Parse ``--output terse`` output for a single sequence.

    Tolerant of what real installs print: ``#`` comment lines, a header
    (with or without a leading ``#``), extra trailing columns such as the
    PSORTb version, spaces instead of tabs, and unrelated log lines. A row
    is a line whose third field is a number. When the output has no usable
    row, the error quotes the start of the output so it can be diagnosed.
    """
    rows = []

    for line in text.splitlines():
        stripped = line.strip()

        if not stripped or stripped.startswith("#"):
            continue

        fields = _split_row(stripped)

        if fields[0].lower() == "seqid":
            continue

        if len(fields) >= 3 and _as_score(fields[2]) is not None:
            rows.append(fields)

    if not rows:
        raise ValueError(
            "Expected a SeqID/Localization/Score row in PSORTb output, "
            f"but found none. Output began: {_snippet(text)}"
        )

    if len({row[0] for row in rows}) != 1:
        raise ValueError(
            "PSORTb output has rows for more than one sequence, but one "
            f"was submitted. Output began: {_snippet(text)}"
        )

    known = {name.lower(): name for name in LOCATION_MAP}
    best = max(rows, key=lambda row: float(row[2]))
    localization = known.get(best[1].lower())

    if localization is None:
        raise ValueError(f"Unrecognised PSORTb localization: {best[1]}")

    return {
        "method": SOURCE,
        "localization": localization,
        "location": LOCATION_MAP[localization],
        "score": float(best[2]),
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


def _resolve_backend() -> str:
    backend = os.environ.get("PSORTB_BACKEND", "local").strip().lower()

    if backend not in VALID_BACKENDS:
        raise ValueError(
            "PSORTB_BACKEND must be one of: "
            + ", ".join(sorted(VALID_BACKENDS))
        )

    return backend


def _resolve_gram(gram: str | None) -> str:
    gram = (gram or os.environ.get("PSORTB_GRAM", "negative")).lower()

    if gram not in VALID_GRAM:
        raise ValueError(
            "PSORTB_GRAM must be one of: " + ", ".join(sorted(VALID_GRAM))
        )

    return gram


def _local_command(fasta: Path, results: Path, gram: str) -> list[str]:
    configured = os.environ.get("PSORTB_EXECUTABLE", "").strip()
    executable = configured or shutil.which("psort")

    if not executable or not (
        shutil.which(executable) or os.path.isfile(executable)
    ):
        raise NotConfigured(
            "PSORTb is switched on but no psort executable was found"
            + (f" at {configured}" if configured else "")
            + ". Set PSORTB_BACKEND=docker to use the "
            "brinkmanlab/psortb_commandline image, set PSORTB_EXECUTABLE to "
            "a local install, or set PSORTB_ENABLED=0."
        )

    return [executable, VALID_GRAM[gram], "-o", "terse",
            "-r", str(results), "-i", str(fasta)]


def _docker_command(fasta: Path, results: Path, gram: str) -> list[str]:
    configured = os.environ.get("DOCKER_EXECUTABLE", "").strip() or "docker"

    if not (shutil.which(configured) or os.path.isfile(configured)):
        raise NotConfigured(
            "PSORTb is switched on with PSORTB_BACKEND=docker but the "
            f"docker command was not found ({configured}). Install Docker, "
            "set DOCKER_EXECUTABLE, or set PSORTB_ENABLED=0."
        )

    image = os.environ.get("PSORTB_DOCKER_IMAGE", "").strip() or (
        DEFAULT_DOCKER_IMAGE
    )

    # The input file sits in the mounted results directory, as the image's
    # own wrapper script arranges it. MOUNT is the host path the image's
    # wrapper passes through.
    return [
        configured, "run", "--rm",
        "-v", f"{results}:{DOCKER_RESULTS_DIR}",
        "-e", f"MOUNT={results}",
        image,
        DOCKER_PSORT_PATH, VALID_GRAM[gram], "-o", "terse",
        "-r", DOCKER_RESULTS_DIR,
        "-i", f"{DOCKER_RESULTS_DIR}/{fasta.name}",
    ]


def run_psortb(sequence: str, gram: str | None = None) -> dict:
    gram = _resolve_gram(gram)
    backend = _resolve_backend()

    with tempfile.TemporaryDirectory(
        prefix="psortb-", ignore_cleanup_errors=True
    ) as workdir:
        results = Path(workdir) / "results"
        results.mkdir()
        # Docker may run as a different user, so let it write here.
        results.chmod(0o777)
        fasta = results / "query.fasta"
        fasta.write_text(f">query\n{sequence}\n")

        command = (
            _docker_command(fasta, results, gram)
            if backend == "docker"
            else _local_command(fasta, results, gram)
        )

        try:
            completed = subprocess.run(
                command,
                text=True,
                capture_output=True,
                check=True,
                timeout=_timeout_seconds(),
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
        # standard output for wrappers that print it instead. The input
        # FASTA lives in the same directory and is not a report. Try each
        # candidate in turn so stray log files cannot hide the report.
        candidates = [
            path.read_text(errors="replace")
            for path in sorted(results.glob("*terse*"))
            + sorted(results.glob("*.txt"))
        ]
        candidates.append(completed.stdout or "")

    prediction = None
    first_error = None

    for output in candidates:
        if not output.strip():
            continue

        try:
            prediction = parse_terse_output(output)
            break
        except ValueError as error:
            first_error = first_error or error

    if prediction is None:
        raise first_error or ValueError(
            "PSORTb finished but produced no output to read."
        )

    prediction["gram"] = gram
    prediction["backend"] = backend
    return prediction


def fetch_psortb_prediction(sequence: str) -> dict:
    """Run PSORTb; report failures instead of raising."""
    try:
        return {"status": "completed", **run_psortb(sequence)}
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
            "message": str(error) or "PSORTb failed.",
        }
