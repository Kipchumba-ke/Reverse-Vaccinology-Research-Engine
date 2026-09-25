import pytest

from app.analysis.blast import parse_blast_hit, parse_blast_tabular_hit


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


from app.analysis.pipeline import analyze_protein
from app.reporting.report import generate_protein_report


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
