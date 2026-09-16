from app.analysis.pipeline import analyze_protein
from app.analysis.localization import (
    create_localization_evidence,
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