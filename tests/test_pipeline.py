from app.analysis.pipeline import analyze_protein
from app.analysis.localization import (
    create_localization_evidence,
)
from app.analysis.essentiality import (
    create_essentiality_evidence
)
from app.analysis.host_similarity import (
    create_host_similarity_evidence
)


def test_pipeline_normalizes_sequence():
    result = analyze_protein("mktii\nals")

    assert result.sequence == "MKTIIALS"
    assert result.length == 8


def test_pipeline_returns_core_analysis():
    result = analyze_protein(
        "MKTIIALSYIFCLVFADYKDDDDK"
    )

    assert result.length == 24
    assert "counts" in result.composition
    assert "percentages" in result.composition

    assert result.molecular_weight > 0
    assert isinstance(result.gravy, float)

    assert 0 <= result.isoelectric_point <= 14

    assert "positively_charged" in (
        result.charge_and_hydrophobicity
    )

    assert isinstance(
        result.hydrophobic_regions,
        list,
    )

    assert isinstance(
        result.transmembrane_candidates,
        list,
    )


def test_pipeline_result_can_be_converted_to_dict():
    result = analyze_protein("MKTIIALS")

    data = result.to_dict()

    assert isinstance(data, dict)
    assert data["sequence"] == "MKTIIALS"
    assert data["length"] == 8
    assert "composition" in data
    assert "molecular_weight" in data
    assert "gravy" in data
    assert "isoelectric_point" in data


def test_pipeline_rejects_invalid_sequence():
    import pytest

    with pytest.raises(ValueError):
        analyze_protein("MKTIIALS!")


def test_pipeline_rejects_empty_sequence():
    import pytest

    with pytest.raises(ValueError):
        analyze_protein("")

def test_pipeline_handles_short_sequences():
    result = analyze_protein("MKTIIALS")

    assert result.sequence == "MKTIIALS"
    assert result.length == 8

    assert result.hydrophobic_regions == []
    assert result.transmembrane_candidates == []

def test_pipeline_includes_hydropathy_profile():
    result = analyze_protein(
        "MKTIIALSYIFCLVFADYKDDDDK"
    )

    assert isinstance(
        result.hydropathy_profile,
        list,
    )

    assert len(result.hydropathy_profile) == (
        result.length - 19 + 1
    )


def test_hydropathy_profile_contains_expected_fields():
    result = analyze_protein(
        "MKTIIALSYIFCLVFADYKDDDDK"
    )

    first_window = result.hydropathy_profile[0]

    assert "start" in first_window
    assert "end" in first_window
    assert "hydropathy" in first_window


def test_short_sequence_has_no_hydropathy_profile():
    result = analyze_protein("MKTIIALS")

    assert result.hydropathy_profile == []


def test_hydropathy_profile_is_in_to_dict():
    result = analyze_protein(
        "MKTIIALSYIFCLVFADYKDDDDK"
    )

    data = result.to_dict()

    assert "hydropathy_profile" in data
    assert isinstance(
        data["hydropathy_profile"],
        list,
    )

def test_pipeline_accepts_localization_evidence():
    evidence = create_localization_evidence(
        location="outer_membrane",
        source="PredictionTool",
        confidence="high",
        description="Predicted outer-membrane localization.",
    )

    result = analyze_protein(
        "MKTIIALSYIFCLVFADYKDDDDK",
        localization_evidence=[evidence],
    )

    assert len(result.localization_evidence) == 1

    assert (
        result.localization_evidence[0].location
        == "outer_membrane"
    )


def test_pipeline_has_empty_localization_evidence_by_default():
    result = analyze_protein("MKTIIALSYIFCLVFADYKDDDDK")

    assert result.localization_evidence == []


def test_localization_evidence_is_in_to_dict():
    evidence = create_localization_evidence(
        location="periplasm",
        source="PredictionTool",
        confidence="medium",
        description="Predicted periplasmic localization.",
    )

    result = analyze_protein(
        "MKTIIALSYIFCLVFADYKDDDDK",
        localization_evidence=[evidence],
    )

    data = result.to_dict()

    assert len(data["localization_evidence"]) == 1

    assert (
        data["localization_evidence"][0]["location"]
        == "periplasm"
    )

    assert (
        data["localization_evidence"][0]["source"]
        == "PredictionTool"
    )

def test_pipeline_accepts_essentiality_evidence():
    evidence = create_essentiality_evidence(
        gene_id="geneA",
        organism="Example bacterium",
        essentiality_status="essential",
        source="Experimental knockout study",
        confidence="high",
        description="Loss of the gene prevented viable growth.",
    )

    result = analyze_protein(
        "MKTIIALSYIFCLVFAD",
        essentiality_evidence=[evidence],
    )

    assert len(result.essentiality_evidence) == 1
    assert (
        result.essentiality_evidence[0].essentiality_status
        == "essential"
    )

def test_pipeline_defaults_to_empty_essentiality_evidence():
    result = analyze_protein("MKTIIALSYIFCLVFAD")

    assert result.essentiality_evidence == []

def test_pipeline_accepts_host_similarity_evidence():
    evidence = create_host_similarity_evidence(
        target_id="pathogen_gene_A",
        host_id="host_protein_123",
        similarity_method="BLASTP",
        identity_percentage=18.5,
        alignment_length=142,
        query_coverage_percentage=80.0,
        subject_coverage_percentage=75.0,
        e_value=0.42,
        source="Host protein database",
        confidence="medium",
        description="Low sequence similarity was observed.",
    )

    result = analyze_protein(
        "MKTIIALSYIFCLVFAD",
        host_similarity_evidence=[evidence],
    )

    assert len(result.host_similarity_evidence) == 1
    assert (
        result.host_similarity_evidence[0].target_id
        == "pathogen_gene_A"
    )

def test_pipeline_defaults_to_empty_host_similarity_evidence():
    result = analyze_protein("MKTIIALSYIFCLVFAD")

    assert result.host_similarity_evidence == []

def test_pipeline_preserves_protein_id():
    result = analyze_protein(
        "MKTIIALSYIFCLVFAD",
        protein_id="protein_1",
    )

    assert result.protein_id == "protein_1"

def test_pipeline_to_dict_preserves_protein_id():
    result = analyze_protein(
        "MKTIIALSYIFCLVFAD",
        protein_id="protein_1",
    )

    data = result.to_dict()

    assert data["protein_id"] == "protein_1"


def test_pipeline_includes_peptide_candidates():
    result = analyze_protein(
        "MKTIIALSYIFCLVFADYKDDDDK"
    )

    assert isinstance(
        result.peptide_candidates,
        list,
    )

    assert len(result.peptide_candidates) > 0

    first_candidate = result.peptide_candidates[0]

    assert "start" in first_candidate
    assert "end" in first_candidate
    assert "sequence" in first_candidate


def test_analyze_protein_calculates_conservation_from_aligned_sequences():
    result = analyze_protein(
        "ACDE",
        aligned_sequences=[
            "ACDE-",
            "ACD--",
        ],
    )

    assert result.conservation_columns
    assert result.conservation_columns[0]["position"] == 1
    assert result.conservation_columns[0]["conserved"] is True


def test_analyze_protein_calculates_conservation_summary_from_alignment():
    result = analyze_protein(
        "ACDE",
        aligned_sequences=[
            "ACDE-",
            "ACD--",
        ],
    )

    assert result.conservation_columns
    assert result.conservation_columns[0]["conserved"] is True