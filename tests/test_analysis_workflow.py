import pytest
from app.analysis.workflow import (
    analyze_fasta,
    analyze_fasta_records,
)
from app.models.workflow_result import AnalysisWorkflowResult


def test_analyze_fasta_records_returns_alignment_and_conservation():
    records = [
        {"id": "protein_1", "sequence": "MKT"},
        {"id": "protein_2", "sequence": "MKTT"},
        {"id": "protein_3", "sequence": "MKT"},
    ]

    result = analyze_fasta_records(records)

    assert result.records == records

    assert result.alignment == [
        "MK-T",
        "MKTT",
        "MK-T",
    ]

    assert result.conservation.sequence_count == 3
    assert result.conservation.alignment_length == 4
    assert result.conservation.conserved_positions == 3
    assert result.conservation.conservation_percentage == 75.0
    assert result.conservation.mean_identity == 100.0

def test_analyze_fasta_records_rejects_empty_records():
    with pytest.raises(
        ValueError,
        match="At least one FASTA record is required",
    ):
        analyze_fasta_records([])

def test_analyze_fasta_records_rejects_missing_sequence():
    records = [
        {"id": "protein_1"},
    ]

    with pytest.raises(
        ValueError,
        match="FASTA record must contain id and sequence",
    ):
        analyze_fasta_records(records)

def test_analyze_fasta_records_rejects_invalid_sequence():
    records = [
        {"id": "protein_1", "sequence": "MKXZ"},
        {"id": "protein_2", "sequence": "MKT"},
    ]

    with pytest.raises(
        ValueError,
        match="Invalid amino acid characters found",
    ):
        analyze_fasta_records(records)

def test_analysis_workflow_result_stores_analysis_outputs():
    records = [
        {"id": "protein_1", "sequence": "MKT"},
        {"id": "protein_2", "sequence": "MKTT"},
        {"id": "protein_3", "sequence": "MKT"},
    ]

    result = analyze_fasta_records(records)

    assert isinstance(result, AnalysisWorkflowResult)
    assert result.records == records
    assert result.alignment == [
        "MK-T",
        "MKTT",
        "MK-T",
    ]
    assert result.conservation.sequence_count == 3

def test_analysis_workflow_result_can_be_serialized():
    records = [
        {"id": "protein_1", "sequence": "MKT"},
        {"id": "protein_2", "sequence": "MKTT"},
        {"id": "protein_3", "sequence": "MKT"},
    ]

    result = analyze_fasta_records(records)

    serialized = result.to_dict()

    assert serialized["records"] == records
    assert serialized["alignment"] == [
        "MK-T",
        "MKTT",
        "MK-T",
    ]
    assert serialized["conservation"]["sequence_count"] == 3
    assert serialized["conservation"]["alignment_length"] == 4

def test_analyze_fasta_parses_and_analyzes_multiple_records():
    fasta_text = """>protein_1
MKT
>protein_2
MKTT
>protein_3
MKT
"""

    result = analyze_fasta(fasta_text)

    assert result.records == [
        {"id": "protein_1", "sequence": "MKT"},
        {"id": "protein_2", "sequence": "MKTT"},
        {"id": "protein_3", "sequence": "MKT"},
    ]

    assert result.alignment == [
        "MK-T",
        "MKTT",
        "MK-T",
    ]

    assert result.conservation.sequence_count == 3

def test_analyze_fasta_rejects_invalid_fasta():
    fasta_text = """protein_1
MKT
"""

    with pytest.raises(
        ValueError,
        match="Invalid FASTA input",
    ):
        analyze_fasta(fasta_text)

def test_analyze_fasta_rejects_empty_input():
    with pytest.raises(
        ValueError,
        match="Invalid FASTA input",
    ):
        analyze_fasta("")