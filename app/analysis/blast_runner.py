import os
import shutil
import subprocess


def run_blastp(sequence: str, database: str):
    if not database:
        raise ValueError(
            "BLAST database is required."
        )

    blastp = os.environ.get("BLASTP_EXECUTABLE") or shutil.which("blastp")

    if blastp is None:
        raise RuntimeError(
            "blastp executable not found."
        )

    try:
        result = subprocess.run(
            [
                blastp,
                "-query",
                "-",
                "-db",
                database,
                "-outfmt",
                "6 qseqid sseqid pident length qlen slen evalue",
            ],
            input=sequence,
            text=True,
            capture_output=True,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        error_message = (exc.stderr or "").strip()

        if error_message:
            raise RuntimeError(
                f"BLASTP execution failed: {error_message}"
            ) from exc

        raise RuntimeError(
            "BLASTP execution failed."
        ) from exc

    return result.stdout

SHORT_PEPTIDE_OUTFMT = (
    "6 qseqid sseqid pident length qlen slen evalue "
    "qstart qend sstart send"
)


def build_blastp_short_command(blastp: str, database: str) -> list[str]:
    """Command line for searching short peptides against a protein database.

    Whole-protein BLASTP defaults (BLOSUM62, word size 3, strict E-value)
    miss short matches. These are the short-query settings recommended in
    the NCBI BLAST documentation: the blastp-short task, PAM30, word size 2,
    a permissive E-value and composition-based statistics off.
    """
    return [
        blastp,
        "-task", "blastp-short",
        "-query", "-",
        "-db", database,
        "-matrix", "PAM30",
        "-word_size", "2",
        "-evalue", "20000",
        "-comp_based_stats", "0",
        "-max_hsps", "1",
        "-outfmt", SHORT_PEPTIDE_OUTFMT,
    ]


def run_blastp_short(fasta_queries: str, database: str) -> str:
    """Search multi-FASTA peptide queries; returns raw tabular output."""
    if not database:
        raise ValueError("BLAST database is required.")

    blastp = os.environ.get("BLASTP_EXECUTABLE") or shutil.which("blastp")

    if blastp is None:
        raise RuntimeError("blastp executable not found.")

    try:
        result = subprocess.run(
            build_blastp_short_command(blastp, database),
            input=fasta_queries,
            text=True,
            capture_output=True,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        error_message = (exc.stderr or "").strip()

        if error_message:
            raise RuntimeError(
                f"BLASTP short-peptide search failed: {error_message}"
            ) from exc

        raise RuntimeError("BLASTP short-peptide search failed.") from exc

    return result.stdout
