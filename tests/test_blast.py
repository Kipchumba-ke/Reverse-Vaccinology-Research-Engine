import pytest

from app.analysis.blast import (
    parse_blast_hit,
    parse_blast_tabular_hit,
    parse_blast_tabular_output,
    run_blast_analysis,
)
from app.analysis.pipeline import analyze_protein
from app.reporting.report import generate_protein_report
from app.analysis.interpretation import interpret_host_similarity


def test_parse_blast_hit_creates_host_similarity_evidence():
    hit = {
        "query_id": "pathogen_protein_1",
        "subject_id": "human_protein_123",
        "identity_percentage": 18.5,
        "alignment_length": 142,
        "query_coverage_percentage": 80.0,
        "subject_coverage_percentage": 75.0,
        "e_value": 0.42,
    }

    evidence = parse_blast_hit(
        hit,
        source="BLASTP / Host protein database",
        confidence="medium",
        description="BLASTP sequence similarity was observed.",
    )

    assert evidence.target_id == "pathogen_protein_1"
    assert evidence.host_id == "human_protein_123"
    assert evidence.similarity_method == "BLASTP"
    assert evidence.identity_percentage == 18.5
    assert evidence.alignment_length == 142
    assert evidence.query_coverage_percentage == 80.0
    assert evidence.subject_coverage_percentage == 75.0
    assert evidence.e_value == 0.42
    assert evidence.source == "BLASTP / Host protein database"



def test_parse_blast_tabular_hit():
    line = (
        "pathogen_protein_1\t"
        "human_protein_123\t"
        "18.5\t"
        "142\t"
        "180\t"
        "190\t"
        "0.42"
    )

    evidence = parse_blast_tabular_hit(
        line,
        source="BLASTP / Host protein database",
        confidence="medium",
        description="BLASTP sequence similarity was observed.",
    )

    assert evidence.target_id == "pathogen_protein_1"
    assert evidence.host_id == "human_protein_123"
    assert evidence.similarity_method == "BLASTP"
    assert evidence.identity_percentage == 18.5
    assert evidence.alignment_length == 142
    assert evidence.query_coverage_percentage == 78.88888888888889
    assert evidence.subject_coverage_percentage == 74.73684210526315
    assert evidence.e_value == 0.42


def test_parse_blast_tabular_hit_rejects_wrong_number_of_fields():
    line = "pathogen_protein_1\thuman_protein_123\t18.5"

    with pytest.raises(ValueError, match="7 fields"):
        parse_blast_tabular_hit(
            line,
            source="BLASTP / Host protein database",
            confidence="medium",
            description="BLASTP sequence similarity was observed.",
        )


def test_parse_blast_tabular_hit_rejects_zero_sequence_length():
    line = (
        "pathogen_protein_1\t"
        "human_protein_123\t"
        "18.5\t"
        "142\t"
        "0\t"
        "190\t"
        "0.42"
    )

    with pytest.raises(ValueError, match="sequence length"):
        parse_blast_tabular_hit(
            line,
            source="BLASTP / Host protein database",
            confidence="medium",
            description="BLASTP sequence similarity was observed.",
        )



def test_blast_evidence_flows_into_analysis_report():
    hit = {
        "query_id": "pathogen_protein_1",
        "subject_id": "human_protein_123",
        "identity_percentage": 18.5,
        "alignment_length": 142,
        "query_coverage_percentage": 80.0,
        "subject_coverage_percentage": 75.0,
        "e_value": 0.42,
    }

    evidence = parse_blast_hit(
        hit,
        source="BLASTP / Host protein database",
        confidence="medium",
        description="BLASTP sequence similarity was observed.",
    )

    result = analyze_protein(
        "MKTIIALSYIFCLVFAD",
        host_similarity_evidence=[evidence],
    )

    report = generate_protein_report(result)

    host_hits = report["evidence"]["host_similarity"]

    assert len(host_hits) == 1
    assert host_hits[0]["target_id"] == "pathogen_protein_1"
    assert host_hits[0]["host_id"] == "human_protein_123"
    assert host_hits[0]["similarity_method"] == "BLASTP"
    assert host_hits[0]["identity_percentage"] == 18.5
    assert host_hits[0]["e_value"] == 0.42

def test_parse_blast_tabular_output_returns_multiple_evidence_records():
    output = (
        "pathogen_1\thuman_123\t18.5\t142\t180\t190\t0.42\n"
        "pathogen_1\thuman_456\t25.0\t95\t180\t210\t1.2\n"
    )

    evidence = parse_blast_tabular_output(
        output,
        source="NCBI BLASTP",
        confidence="medium",
        description="BLASTP similarity against a host protein database.",
    )

    assert len(evidence) == 2
    assert evidence[0].host_id == "human_123"
    assert evidence[1].host_id == "human_456"


def test_run_blast_analysis_returns_parsed_evidence(monkeypatch):
    output = (
        "pathogen_1\thuman_123\t18.5\t142\t180\t190\t0.42\n"
        "pathogen_1\thuman_456\t25.0\t95\t180\t210\t1.2\n"
    )

    monkeypatch.setattr(
        "app.analysis.blast.run_blastp",
        lambda sequence, database: output,
    )

    evidence = run_blast_analysis(
        "MKTIIALSYIFCLVFAD",
        database="/path/to/host_database",
        source="NCBI BLASTP",
        confidence="medium",
        description="BLASTP similarity against a host protein database.",
    )

    assert len(evidence) == 2
    assert evidence[0].host_id == "human_123"
    assert evidence[1].host_id == "human_456"


def test_run_blast_analysis_returns_empty_list_when_no_hits(monkeypatch):
    monkeypatch.setattr(
        "app.analysis.blast.run_blastp",
        lambda sequence, database: "",
    )

    evidence = run_blast_analysis(
        "MKTIIALSYIFCLVFAD",
        database="/path/to/host_database",
        source="NCBI BLASTP",
        confidence="medium",
        description="BLASTP similarity against a host protein database.",
    )

    assert evidence == []


def test_blast_evidence_can_be_passed_into_protein_analysis(monkeypatch):
    monkeypatch.setattr(
        "app.analysis.blast.run_blastp",
        lambda sequence, database: (
            "pathogen_1\thuman_123\t18.5\t142\t180\t190\t0.42\n"
        ),
    )

    blast_evidence = run_blast_analysis(
        "MKTIIALSYIFCLVFAD",
        database="/path/to/host_database",
        source="NCBI BLASTP",
        confidence="medium",
        description="BLASTP similarity against a host protein database.",
    )

    result = analyze_protein(
        "MKTIIALSYIFCLVFAD",
        host_similarity_evidence=blast_evidence,
    )

    assert len(result.host_similarity_evidence) == 1
    assert result.host_similarity_evidence[0].host_id == "human_123"

def test_run_blast_analysis_rejects_empty_sequence(monkeypatch):
    def fake_run_blastp(*args, **kwargs):
        raise AssertionError("BLAST should not run for an empty sequence")

    monkeypatch.setattr(
        "app.analysis.blast.run_blastp",
        fake_run_blastp,
    )

    with pytest.raises(ValueError, match="Sequence is required"):
        run_blast_analysis(
            "",
            database="test_db",
            source="NCBI",
            confidence="high",
            description="BLAST host similarity search",
        )


def test_run_blast_analysis_rejects_missing_database(monkeypatch):
    def fake_run_blastp(*args, **kwargs):
        raise AssertionError("BLAST should not run without a database")

    monkeypatch.setattr(
        "app.analysis.blast.run_blastp",
        fake_run_blastp,
    )

    with pytest.raises(ValueError, match="BLAST database is required"):
        run_blast_analysis(
            "MKTAYIAKQRQISFVKSHFSRQ",
            database="",
            source="NCBI",
            confidence="high",
            description="BLAST host similarity search",
        )


def test_run_blast_analysis_propagates_blast_execution_failure(monkeypatch):
    def fake_run_blastp(*args, **kwargs):
        raise RuntimeError("BLASTP execution failed")

    monkeypatch.setattr(
        "app.analysis.blast.run_blastp",
        fake_run_blastp,
    )

    with pytest.raises(RuntimeError, match="BLASTP execution failed"):
        run_blast_analysis(
            "MKTAYIAKQRQISFVKSHFSRQ",
            database="test_db",
            source="NCBI",
            confidence="high",
            description="BLAST host similarity search",
        )


def test_run_blast_analysis_rejects_invalid_confidence(monkeypatch):
    def fake_run_blastp(*args, **kwargs):
        raise AssertionError("BLAST should not run with invalid confidence")

    monkeypatch.setattr(
        "app.analysis.blast.run_blastp",
        fake_run_blastp,
    )

    with pytest.raises(ValueError, match="Confidence must be one of"):
        run_blast_analysis(
            "MKTAYIAKQRQISFVKSHFSRQ",
            database="test_db",
            source="NCBI",
            confidence="certain",
            description="BLAST host similarity search",
        )


def test_blast_host_similarity_can_be_interpreted_without_claiming_safety():
    hit = {
        "query_id": "target",
        "subject_id": "human_protein",
        "identity_percentage": 85.0,
        "alignment_length": 200,
        "query_coverage_percentage": 95.0,
        "subject_coverage_percentage": 90.0,
        "e_value": 1e-50,
    }

    evidence = parse_blast_hit(
        hit,
        source="NCBI",
        confidence="high",
        description="BLAST host similarity search",
    )

    interpretation = interpret_host_similarity([evidence.to_dict()])

    assert "does not establish biological safety" in interpretation.interpretation.lower()


def test_run_blast_analysis_preserves_multiple_hits(monkeypatch):
    blast_output = (
        "target\thost_1\t85.0\t200\t210\t220\t1e-50\n"
        "target\thost_2\t62.0\t180\t210\t200\t2e-20\n"
    )

    def fake_run_blastp(*args, **kwargs):
        return blast_output

    monkeypatch.setattr(
        "app.analysis.blast.run_blastp",
        fake_run_blastp,
    )

    evidence = run_blast_analysis(
        "MKTAYIAKQRQISFVKSHFSRQ",
        database="test_db",
        source="NCBI",
        confidence="high",
        description="BLAST host similarity search",
    )

    assert len(evidence) == 2
    assert evidence[0].host_id == "host_1"
    assert evidence[1].host_id == "host_2"