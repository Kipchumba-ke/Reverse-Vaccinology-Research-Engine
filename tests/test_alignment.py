import pytest
from app.analysis.alignment import align_pair
from app.analysis.conservation import (
    calculate_conservation_summary,
    calculate_conserved_columns,
    find_conserved_regions
)


def test_align_pair_returns_equal_length_sequences():
    result = align_pair(
        "MKT",
        "MKTT",
    )

    assert len(result["sequence_a"]) == len(result["sequence_b"])

def test_align_pair_identical_sequences():
    result = align_pair(
        "MKT",
        "MKT",
    )

    assert result["sequence_a"] == "MKT"
    assert result["sequence_b"] == "MKT"
    assert result["score"] == 3

def test_align_pair_handles_mismatch():
    result = align_pair(
        "MKT",
        "MNT",
    )

    assert result["sequence_a"] == "MKT"
    assert result["sequence_b"] == "MNT"
    assert result["score"] == 1

def test_align_pair_introduces_gap_for_insertion():
    result = align_pair(
        "MKT",
        "MKTT",
    )

    assert result["sequence_a"] == "MK-T"
    assert result["sequence_b"] == "MKTT"

def test_align_pair_gap_alignment_has_correct_score():
    result = align_pair(
        "MKT",
        "MKTT",
    )

    assert result["sequence_a"] == "MK-T"
    assert result["sequence_b"] == "MKTT"
    assert result["score"] == 2

def test_align_pair_accepts_custom_scoring():
    result = align_pair(
        "MKT",
        "MNT",
        match_score=2,
        mismatch_score=-2,
        gap_penalty=-3,
    )

    assert result["sequence_a"] == "MKT"
    assert result["sequence_b"] == "MNT"
    assert result["score"] == 2

def test_align_pair_gap_penalty_affects_alignment():
    result = align_pair(
        "MKT",
        "MKTT",
        match_score=2,
        mismatch_score=-1,
        gap_penalty=-1,
    )

    assert result["sequence_a"] == "MK-T"
    assert result["sequence_b"] == "MKTT"

def test_align_pair_harsh_gap_penalty_can_prefer_mismatch():
    result = align_pair(
        "MKT",
        "MKTT",
        match_score=2,
        mismatch_score=-1,
        gap_penalty=-5,
    )

    assert result["score"] == 1

def test_align_pair_rejects_empty_sequence():
    with pytest.raises(ValueError, match="Sequences cannot be empty"):
        align_pair(
            "",
            "MKT",
        )

def test_align_pair_rejects_invalid_protein_sequence():
    with pytest.raises(ValueError):
        align_pair(
            "MKT123",
            "MKT",
        )

def test_pairwise_alignment_output_can_be_used_for_conservation():
    result = align_pair(
        "MKT",
        "MKT",
    )

    conservation = calculate_conservation_summary(
        [
            result["sequence_a"],
            result["sequence_b"],
        ]
    )

    assert conservation.sequence_count == 2
    assert conservation.alignment_length == 3
    assert conservation.mean_identity == 100.0
    assert conservation.conservation_percentage == 100.0

def test_alignment_with_gap_produces_expected_conservation():
    result = align_pair(
        "MKT",
        "MKTT",
    )

    conservation = calculate_conservation_summary(
        [
            result["sequence_a"],
            result["sequence_b"],
        ]
    )

    assert result["sequence_a"] == "MK-T"
    assert result["sequence_b"] == "MKTT"
    assert conservation.alignment_length == 4
    assert conservation.mean_identity == 100.0
    assert conservation.conservation_percentage == 75.0

def test_alignment_with_gap_identifies_conserved_columns():
    result = align_pair(
        "MKT",
        "MKTT",
    )

    columns = calculate_conserved_columns(
        [
            result["sequence_a"],
            result["sequence_b"],
        ]
    )

    assert [column["conserved"] for column in columns] == [
        True,
        True,
        False,
        True,
    ]

def test_alignment_can_produce_conserved_regions():
    result = align_pair(
        "MKT",
        "MKTT",
    )

    columns = calculate_conserved_columns(
        [
            result["sequence_a"],
            result["sequence_b"],
        ]
    )

    regions = find_conserved_regions(
        columns,
        min_length=2,
    )

    assert regions == [
        {
            "start": 1,
            "end": 2,
            "length": 2,
            "consensus": "MK",
        }
    ]