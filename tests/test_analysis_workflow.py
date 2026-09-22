import pytest
from app.analysis.workflow import (
    analyze_fasta,
    analyze_fasta_records,
)
from app.models.workflow_result import AnalysisWorkflowResult
from app.models.analysis_result import ProteinAnalysisResult
from app.models.localization import LocalizationEvidence
from app.models.essentiality import EssentialityEvidence


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
    assert len(serialized["protein_analyses"]) == 3

    assert [
        analysis["protein_id"]
        for analysis in serialized["protein_analyses"]
    ] == [
        "protein_1",
        "protein_2",
        "protein_3",
    ]

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

def test_analyze_fasta_includes_protein_analyses():
    fasta_text = """>protein_1
MKT
>protein_2
MKTT
>protein_3
MKT
"""

    result = analyze_fasta(fasta_text)

    assert len(result.protein_analyses) == 3

    assert all(
        isinstance(analysis, ProteinAnalysisResult)
        for analysis in result.protein_analyses
    )

    assert [
        analysis.protein_id
        for analysis in result.protein_analyses
    ] == [
        "protein_1",
        "protein_2",
        "protein_3",
    ]

def test_analyze_fasta_records_attaches_localization_evidence():
    records = [
        {"id": "protein_1", "sequence": "MKT"},
        {"id": "protein_2", "sequence": "MKTT"},
    ]

    localization_evidence = {
        "protein_1": [],
        "protein_2": [],
    }

    result = analyze_fasta_records(
        records,
        localization_evidence=localization_evidence,
    )

    assert result.protein_analyses[0].localization_evidence == []
    assert result.protein_analyses[1].localization_evidence == []

def test_analyze_fasta_records_keeps_localization_evidence_with_correct_protein():
    records = [
        {"id": "protein_1", "sequence": "MKT"},
        {"id": "protein_2", "sequence": "MKTT"},
    ]

    evidence = LocalizationEvidence(
        location="surface",
        source="experimental",
        confidence="high",
        description="Located on the cell surface.",
    )

    localization_evidence = {
        "protein_1": [evidence],
        "protein_2": [],
    }

    result = analyze_fasta_records(
        records,
        localization_evidence=localization_evidence,
    )

    assert result.protein_analyses[0].localization_evidence == [evidence]
    assert result.protein_analyses[1].localization_evidence == []

def test_analyze_fasta_accepts_localization_evidence():
    fasta_text = """>protein_1
MKT
>protein_2
MKTT
"""

    evidence = LocalizationEvidence(
        location="surface",
        source="experimental",
        confidence="high",
        description="Located on the cell surface.",
    )

    result = analyze_fasta(
        fasta_text,
        localization_evidence={
            "protein_1": [evidence],
            "protein_2": [],
        },
    )

    assert result.protein_analyses[0].localization_evidence == [evidence]
    assert result.protein_analyses[1].localization_evidence == []

def test_analyze_fasta_serializes_localization_evidence():
    fasta_text = """>protein_1
MKT
>protein_2
MKTT
"""

    evidence = LocalizationEvidence(
        location="surface",
        source="experimental",
        confidence="high",
        description="Located on the cell surface.",
    )

    result = analyze_fasta(
        fasta_text,
        localization_evidence={
            "protein_1": [evidence],
            "protein_2": [],
        },
    )

    serialized = result.to_dict()

    assert serialized["protein_analyses"][0][
        "localization_evidence"
    ] == [
        {
            "location": "surface",
            "source": "experimental",
            "confidence": "high",
            "description": "Located on the cell surface.",
        }
    ]

    assert serialized["protein_analyses"][1][
        "localization_evidence"
    ] == []

def test_analyze_fasta_records_attaches_essentiality_evidence():
    records = [
        {"id": "protein_1", "sequence": "MKT"},
        {"id": "protein_2", "sequence": "MKTT"},
    ]

    evidence = EssentialityEvidence(
        gene_id="gene_1",
        organism="Test organism",
        essentiality_status="essential",
        source="experimental",
        confidence="high",
        description="Required for survival.",
    )

    essentiality_evidence = {
        "protein_1": [evidence],
        "protein_2": [],
    }

    result = analyze_fasta_records(
        records,
        essentiality_evidence=essentiality_evidence,
    )

    assert result.protein_analyses[0].essentiality_evidence == [evidence]
    assert result.protein_analyses[1].essentiality_evidence == []

def test_analyze_fasta_records_keeps_essentiality_evidence_with_correct_protein():
    records = [
        {"id": "protein_1", "sequence": "MKT"},
        {"id": "protein_2", "sequence": "MKTT"},
    ]

    evidence = EssentialityEvidence(
        gene_id="gene_1",
        organism="Test organism",
        essentiality_status="essential",
        source="experimental",
        confidence="high",
        description="Required for survival.",
    )

    result = analyze_fasta_records(
        records,
        essentiality_evidence={
            "protein_1": [evidence],
            "protein_2": [],
        },
    )

    assert result.protein_analyses[0].essentiality_evidence == [evidence]
    assert result.protein_analyses[1].essentiality_evidence == []

def test_analyze_fasta_accepts_essentiality_evidence():
    fasta_text = """>protein_1
MKT
>protein_2
MKTT
"""

    evidence = EssentialityEvidence(
        gene_id="gene_1",
        organism="Test organism",
        essentiality_status="essential",
        source="experimental",
        confidence="high",
        description="Required for survival.",
    )

    result = analyze_fasta(
        fasta_text,
        essentiality_evidence={
            "protein_1": [evidence],
            "protein_2": [],
        },
    )

    assert result.protein_analyses[0].essentiality_evidence == [evidence]
    assert result.protein_analyses[1].essentiality_evidence == []

def test_analyze_fasta_serializes_essentiality_evidence():
    fasta_text = """>protein_1
MKT
>protein_2
MKTT
"""

    evidence = EssentialityEvidence(
        gene_id="gene_1",
        organism="Test organism",
        essentiality_status="essential",
        source="experimental",
        confidence="high",
        description="Required for survival.",
    )

    result = analyze_fasta(
        fasta_text,
        essentiality_evidence={
            "protein_1": [evidence],
            "protein_2": [],
        },
    )

    serialized = result.to_dict()

    assert serialized["protein_analyses"][0][
        "essentiality_evidence"
    ] == [
        {
            "gene_id": "gene_1",
            "organism": "Test organism",
            "essentiality_status": "essential",
            "source": "experimental",
            "confidence": "high",
            "description": "Required for survival.",
        }
    ]

    assert serialized["protein_analyses"][1][
        "essentiality_evidence"
    ] == []