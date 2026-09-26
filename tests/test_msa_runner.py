import pytest
import subprocess

from app.integrations.msa import run_msa


def test_run_msa_requires_sequences():
    with pytest.raises(ValueError, match="At least two sequences are required"):
        run_msa([])

def test_run_msa_executes_clustalo(monkeypatch):
    calls = {}

    def fake_run(*args, **kwargs):
        calls["args"] = args
        calls["kwargs"] = kwargs

        class Result:
            stdout = ">seq1\nACDE-\n>seq2\nACD-E\n"

        return Result()

    monkeypatch.setattr("app.integrations.msa.subprocess.run", fake_run)

    sequences = [
        "ACDE",
        "ACDE",
    ]

    result = run_msa(sequences)

    assert result == ["ACDE-", "ACD-E"]
    assert result == ["ACDE-", "ACD-E"]
    assert calls["args"][0][0] == "clustalo"
    assert calls["kwargs"]["input"] == ">seq1\nACDE\n>seq2\nACDE\n"


def test_run_msa_reports_clustalo_failure(monkeypatch):
    def fake_run(*args, **kwargs):
        raise subprocess.CalledProcessError(
            returncode=1,
            cmd=["clustalo"],
            stderr="Clustal Omega failed",
        )

    monkeypatch.setattr("app.integrations.msa.subprocess.run", fake_run)

    with pytest.raises(RuntimeError, match="MSA execution failed"):
        run_msa(["ACDE", "ACDE"])


def test_run_msa_reports_missing_clustalo(monkeypatch):
    def fake_run(*args, **kwargs):
        raise FileNotFoundError("clustalo not found")

    monkeypatch.setattr("app.integrations.msa.subprocess.run", fake_run)

    with pytest.raises(RuntimeError, match="Clustal Omega executable not found"):
        run_msa(["ACDE", "ACDE"])


def test_run_msa_returns_aligned_sequences(monkeypatch):
    def fake_run(*args, **kwargs):
        class Result:
            stdout = ">seq1\nACDE-\n>seq2\nACD-E\n"

        return Result()

    monkeypatch.setattr("app.integrations.msa.subprocess.run", fake_run)

    result = run_msa(["ACDE", "ACDE"])

    assert result == ["ACDE-", "ACD-E"]

def test_run_msa_rejects_empty_output(monkeypatch):
    def fake_run(*args, **kwargs):
        class Result:
            stdout = ""

        return Result()

    monkeypatch.setattr("app.integrations.msa.subprocess.run", fake_run)

    with pytest.raises(RuntimeError, match="MSA returned no alignment"):
        run_msa(["ACDE", "ACDE"])


def test_run_msa_alignment_can_be_used_for_conservation(monkeypatch):
    def fake_run(*args, **kwargs):
        class Result:
            stdout = ">seq1\nACDE-\n>seq2\nACD--\n"

        return Result()

    monkeypatch.setattr("app.integrations.msa.subprocess.run", fake_run)

    aligned_sequences = run_msa(["ACDE", "ACD"])

    from app.analysis.conservation import calculate_conserved_columns

    conserved_columns = calculate_conserved_columns(aligned_sequences)

    assert [column["position"] for column in conserved_columns if column["conserved"]] == [1, 2, 3]