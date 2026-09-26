import shutil
import subprocess


def run_blastp(sequence: str, database: str):
    if not database:
        raise ValueError(
            "BLAST database is required."
        )

    blastp = shutil.which("blastp")

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