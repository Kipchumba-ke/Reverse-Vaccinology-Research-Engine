import pytest
import subprocess

from app.analysis.blast_runner import run_blastp
from app.analysis.blast import parse_blast_tabular_hit


def test_run_blastp_requires_blastp_executable(monkeypatch):
    monkeypatch.setattr(
        "app.analysis.blast_runner.shutil.which",
        lambda executable: None,
    )

    with pytest.raises(
        RuntimeError,
        match="blastp executable not found",
    ):
        run_blastp(
            "MKTIIALSYIFCLVFAD",
            database="/path/to/host_database",
        )


def test_run_blastp_returns_tabular_output(monkeypatch):
    class CompletedProcess:
        stdout = (
            "pathogen_protein_1\thuman_protein_123\t18.5\t142\t"
            "180\t190\t0.42\n"
        )

    monkeypatch.setattr(
        "app.analysis.blast_runner.shutil.which",
        lambda executable: "/usr/bin/blastp",
    )

    def fake_run(*args, **kwargs):
        assert args[0][0] == "/usr/bin/blastp"
        return CompletedProcess()

    monkeypatch.setattr(
        "app.analysis.blast_runner.subprocess.run",
        fake_run,
    )

    output = run_blastp(
        "MKTIIALSYIFCLVFAD",
        database="/path/to/host_database",
    )

    assert output == (
        "pathogen_protein_1\thuman_protein_123\t18.5\t142\t"
        "180\t190\t0.42\n"
    )


def test_run_blastp_reports_execution_failure(monkeypatch):
    monkeypatch.setattr(
        "app.analysis.blast_runner.shutil.which",
        lambda executable: "/usr/bin/blastp",
    )

    def fake_run(*args, **kwargs):
        raise subprocess.CalledProcessError(
            returncode=1,
            cmd=args[0],
        )

    monkeypatch.setattr(
        "app.analysis.blast_runner.subprocess.run",
        fake_run,
    )

    with pytest.raises(RuntimeError, match="BLASTP execution failed"):
        run_blastp(
            "MKTIIALSYIFCLVFAD",
            database="/path/to/host_database",
        )


def test_run_blastp_allows_empty_output(monkeypatch):
    class CompletedProcess:
        stdout = ""

    monkeypatch.setattr(
        "app.analysis.blast_runner.shutil.which",
        lambda executable: "/usr/bin/blastp",
    )

    monkeypatch.setattr(
        "app.analysis.blast_runner.subprocess.run",
        lambda *args, **kwargs: CompletedProcess(),
    )

    output = run_blastp(
        "MKTIIALSYIFCLVFAD",
        database="/path/to/host_database"
    )

    assert output == ""



def test_blast_runner_output_can_be_parsed_into_evidence(monkeypatch):
    class CompletedProcess:
        stdout = (
            "pathogen_1\thuman_123\t18.5\t142\t180\t190\t0.42\n"
        )

    monkeypatch.setattr(
        "app.analysis.blast_runner.shutil.which",
        lambda executable: "/usr/bin/blastp",
    )

    monkeypatch.setattr(
        "app.analysis.blast_runner.subprocess.run",
        lambda *args, **kwargs: CompletedProcess(),
    )

    output = run_blastp(
        "MKTIIALSYIFCLVFAD",
        database="/path/to/host_database",
    )

    evidence = parse_blast_tabular_hit(
        output.strip(),
        source="NCBI BLASTP",
        confidence="medium",
        description="BLASTP similarity against a host protein database.",
    )

    assert evidence.target_id == "pathogen_1"
    assert evidence.host_id == "human_123"
    assert evidence.identity_percentage == 18.5
    assert evidence.alignment_length == 142


def test_run_blastp_requires_database(monkeypatch):
    monkeypatch.setattr(
        "app.analysis.blast_runner.shutil.which",
        lambda executable: "/usr/bin/blastp",
    )

    with pytest.raises(
        ValueError,
        match="BLAST database is required",
    ):
        run_blastp("MKTIIALSYIFCLVFAD", database="")


def test_run_blastp_includes_blast_error_message(monkeypatch):
    monkeypatch.setattr(
        "app.analysis.blast_runner.shutil.which",
        lambda executable: "/usr/bin/blastp",
    )

    def fake_run(*args, **kwargs):
        raise subprocess.CalledProcessError(
            returncode=1,
            cmd=args[0],
            stderr="Database does not exist.",
        )

    monkeypatch.setattr(
        "app.analysis.blast_runner.subprocess.run",
        fake_run,
    )

    with pytest.raises(
        RuntimeError,
        match="BLASTP execution failed: Database does not exist.",
    ):
        run_blastp(
            "MKTIIALSYIFCLVFAD",
            database="/path/to/host_database",
        )
