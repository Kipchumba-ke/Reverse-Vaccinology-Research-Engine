"""Helpers shared by the optional predictor adapters.

``NotConfigured`` separates "this tool is switched on but not set up on this
server" from "the tool ran and failed". The report shows the two
differently, so a missing install is not mistaken for a broken analysis.

``run_biolib_app`` runs a BioLib cloud app (DeepTMHMM, SignalP 6) and returns
one output file. BioLib needs you to be signed in. On a server set the
``BIOLIB_TOKEN`` environment variable (create a token in your BioLib account
settings); the ``pybiolib`` package reads it itself.
"""

import os
import tempfile
import threading
from pathlib import Path


class NotConfigured(RuntimeError):
    """The tool is enabled but its install or settings are missing."""


# BioLib resolves input paths against the current directory, so the run
# changes into a temporary one. The working directory belongs to the whole
# process, so concurrent runs in different threads must not overlap.
_BIOLIB_LOCK = threading.Lock()


def env_flag(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {
        "1", "true", "yes", "on",
    }


def run_biolib_app(
    app_name: str,
    args: str,
    fasta_text: str,
    result_pattern: str,
    label: str,
) -> str:
    """Run a BioLib app on ``input.fasta`` and return one result file's text.

    ``args`` is the command line after the app name and may refer to
    ``input.fasta``. ``result_pattern`` is a glob such as ``*.3line``.
    Raises ``NotConfigured`` when pybiolib is missing and ``RuntimeError`` for
    any failure of the run itself.
    """
    # An empty token (for example from an unset compose variable) is not a
    # token; leave it out so BioLib falls back to its saved login.
    if not os.environ.get("BIOLIB_TOKEN", "").strip():
        os.environ.pop("BIOLIB_TOKEN", None)

    try:
        import biolib
    except ImportError as error:
        raise NotConfigured(
            f"{label} is switched on but pybiolib is not installed. "
            "Run: pip install pybiolib"
        ) from error

    with tempfile.TemporaryDirectory(
        prefix="biolib-", ignore_cleanup_errors=True
    ) as workdir:
        with _BIOLIB_LOCK:
            previous = os.getcwd()
            os.chdir(workdir)

            try:
                Path("input.fasta").write_text(fasta_text)
                job = biolib.load(app_name).cli(args=args, blocking=True)
                job.save_files(output_dir="results")
            except Exception as error:  # BioLib raises its own types
                raise RuntimeError(f"{label} run failed: {error}") from error
            finally:
                os.chdir(previous)

        matches = sorted((Path(workdir) / "results").rglob(result_pattern))

        if not matches:
            raise RuntimeError(f"{label} produced no {result_pattern} file.")

        return matches[0].read_text()
