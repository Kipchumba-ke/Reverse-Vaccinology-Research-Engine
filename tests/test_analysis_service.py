import pytest

from app.models.analysis import Analysis
from app.repositories.analysis_repository import AnalysisRepository
from app.services.analysis_service import (
    analyze_sequence,
    analyze_fasta_records,
    create_analysis,
    persist_analysis,
)


def test_analyze_sequence_returns_protein_report():
    sequence = "MKTAYIAKQRQISFVKSHFSRQ"

    report = analyze_sequence(sequence)

    assert "protein" in report
    assert "measurements" in report
    assert "evidence" in report
    assert "interpretations" in report
    assert "candidate_assessment" in report
    assert "limitations" in report
    assert "conservation" in report
    assert "metadata" in report

def test_analyze_sequence_preserves_protein_metadata():
    report = analyze_sequence(
        "MKTAYIAKQRQISFVKSHFSRQ",
        protein_id="sp|P12345|EXAMPLE",
        protein_name="Example protein",
        organism="Escherichia coli",
        accession="P12345",
    )

    assert report["protein"]["id"] == "sp|P12345|EXAMPLE"
    assert report["protein"]["name"] == "Example protein"
    assert report["protein"]["organism"] == "Escherichia coli"
    assert report["protein"]["accession"] == "P12345"

def test_analyze_fasta_records_with_single_record_returns_report():
    records = [
        {
            "id": "sp|P12345|EXAMPLE",
            "description": "Example protein",
            "organism": "Escherichia coli",
            "accession": "P12345",
            "sequence": "MKTAYIAKQRQISFVKSHFSRQ",
        }
    ]

    report = analyze_fasta_records(records)

    assert report["protein"]["id"] == "sp|P12345|EXAMPLE"
    assert report["protein"]["name"] == "Example protein"
    assert report["protein"]["organism"] == "Escherichia coli"
    assert report["protein"]["accession"] == "P12345"

def test_analyze_fasta_records_with_multiple_records_returns_workflow_dict():
    records = [
        {
            "id": "sp|P12345|EXAMPLE1",
            "description": "Example protein 1",
            "organism": "Escherichia coli",
            "accession": "P12345",
            "sequence": "MKTAYIAKQRQISFVKSHFSRQ",
        },
        {
            "id": "sp|P67890|EXAMPLE2",
            "description": "Example protein 2",
            "organism": "Escherichia coli",
            "accession": "P67890",
            "sequence": "MKTAYIAKQRQISFVKSHFSRQ",
        },
    ]

    result = analyze_fasta_records(records)

    assert result["records"] == records
    assert len(result["protein_analyses"]) == 2
    assert result["alignment"] is not None
    assert result["conservation"] is not None


def test_persist_analysis_saves_analysis(db_session):
    repository = AnalysisRepository(db_session)

    analysis = Analysis(
        protein_id="sp|P12345|TEST_PROTEIN",
        protein_name="Test protein",
        organism="Escherichia coli",
        accession="P12345",
        sequence="MKTAYIAKQRQISFVKSHFSRQ",
        status="completed",
    )

    saved = persist_analysis(analysis, repository)

    assert saved == analysis

    persisted = repository.find_by_id(analysis.id)

    assert persisted == analysis


def test_create_analysis_builds_analysis_from_input():
    analysis = create_analysis(
        "MKTAYIAKQRQISFVKSHFSRQ",
        protein_id="sp|P12345|EXAMPLE",
        protein_name="Example protein",
        organism="Escherichia coli",
        accession="P12345",
    )

    assert isinstance(analysis, Analysis)
    assert analysis.protein_id == "sp|P12345|EXAMPLE"
    assert analysis.protein_name == "Example protein"
    assert analysis.organism == "Escherichia coli"
    assert analysis.accession == "P12345"
    assert analysis.sequence == "MKTAYIAKQRQISFVKSHFSRQ"
    assert analysis.status == "pending"


def test_create_analysis_normalizes_sequence():
    analysis = create_analysis(
        " mktay iakqrqisfvkshfsrq ",
    )

    assert analysis.sequence == "MKTAYIAKQRQISFVKSHFSRQ"


def test_create_analysis_rejects_invalid_sequence():
    with pytest.raises(ValueError):
        create_analysis("MKTAY123INVALID")


def test_create_and_persist_analysis_round_trip(db_session):
    repository = AnalysisRepository(db_session)

    analysis = create_analysis(
        " mktay iakqrqisfvkshfsrq ",
        protein_id="sp|P12345|EXAMPLE",
        protein_name="Example protein",
        organism="Escherichia coli",
        accession="P12345",
    )

    persisted = persist_analysis(analysis, repository)

    saved = repository.find_by_id(persisted.id)

    assert saved == analysis
