import pytest

from app.analysis.localization import (
    create_localization_evidence,
)


def test_create_localization_evidence():
    evidence = create_localization_evidence(
        location="outer_membrane",
        source="PredictionTool",
        confidence="high",
        description="Predicted outer-membrane localization.",
    )

    assert evidence.location == "outer_membrane"
    assert evidence.source == "PredictionTool"
    assert evidence.confidence == "high"


def test_localization_evidence_to_dict():
    evidence = create_localization_evidence(
        location="periplasm",
        source="PredictionTool",
        confidence="medium",
        description="Predicted periplasmic localization.",
    )

    result = evidence.to_dict()

    assert result["location"] == "periplasm"
    assert result["source"] == "PredictionTool"
    assert result["confidence"] == "medium"


def test_invalid_location_is_rejected():
    with pytest.raises(ValueError):
        create_localization_evidence(
            location="nucleus",
            source="PredictionTool",
            confidence="high",
            description="Invalid localization.",
        )


def test_invalid_confidence_is_rejected():
    with pytest.raises(ValueError):
        create_localization_evidence(
            location="outer_membrane",
            source="PredictionTool",
            confidence="excellent",
            description="Invalid confidence.",
        )


def test_empty_source_is_rejected():
    with pytest.raises(ValueError):
        create_localization_evidence(
            location="outer_membr=========================================================== 65 passed in 0.14s ============================================================ane",
            source="",
            confidence="high",
            description="Some evidence.",
        )


def test_empty_description_is_rejected():
    with pytest.raises(ValueError):
        create_localization_evidence(
            location="outer_membrane",
            source="PredictionTool",
            confidence="high",
            description="",
        )

def test_localization_strips_are_not_accepted_as_valid_source():
    with pytest.raises(
        ValueError,
        match="source cannot be empty",
    ):
        create_localization_evidence(
            location="outer_membrane",
            source="   ",
            confidence="high",
            description="Some evidence.",
        )


def test_localization_strips_are_not_accepted_as_valid_description():
    with pytest.raises(
        ValueError,
        match="description cannot be empty",
    ):
        create_localization_evidence(
            location="outer_membrane",
            source="PredictionTool",
            confidence="high",
            description="   ",
        )

@pytest.mark.parametrize(
    "location",
    [
        "cytoplasm",
        "inner_membrane",
        "periplasm",
        "outer_membrane",
        "extracellular",
        "unknown",
    ],
)
def test_all_supported_localizations_are_accepted(location):
    evidence = create_localization_evidence(
        location=location,
        source="PredictionTool",
        confidence="medium",
        description="Localization prediction.",
    )

    assert evidence.location == location

