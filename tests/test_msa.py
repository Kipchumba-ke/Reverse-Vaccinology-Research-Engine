import pytest
from app.analysis.msa import align_sequences
from app.analysis.conservation import (
    calculate_conservation_summary,
    calculate_conserved_columns
)


def test_align_sequences_returns_equal_length_alignment():
    sequences = [
        "MKT",
        "MKT",
        "MKT",
    ]

    result = align_sequences(sequences)

    assert len(result) == 3
    assert all(
        len(sequence) == len(result[0])
        for sequence in result
    )

def test_align_sequences_handles_insertion():
    sequences = [
        "MKT",
        "MKTT",
        "MKT",
    ]

    result = align_sequences(sequences)

    assert result == [
        "MK-T",
        "MKTT",
        "MK-T",
    ]

def test_align_sequences_rejects_empty_input():
    with pytest.raises(ValueError, match="At least one sequence"):
        align_sequences([])

def test_align_sequences_preserves_existing_alignment_columns():
    sequences = [
        "MKT",
        "MKTT",
        "MKT",
    ]

    result = align_sequences(sequences)

    assert all(len(sequence) == 4 for sequence in result)

def test_align_sequences_handles_insertion_at_beginning():
    sequences = [
        "MKT",
        "MMKT",
        "MKT",
    ]

    result = align_sequences(sequences)

    assert result == [
        "-MKT",
        "MMKT",
        "-MKT",
    ]

def test_align_sequences_handles_different_insertion_positions():
    sequences = [
        "MKT",
        "MKTT",
        "MMKT",
    ]

    result = align_sequences(sequences)

    assert result == [
        "-MK-T",
        "-MKTT",
        "MMK-T",
    ]

def test_msa_output_can_be_analyzed_for_conserved_columns():
    sequences = [
        "MKT",
        "MKTT",
        "MKT",
    ]

    alignment = align_sequences(sequences)

    conserved_columns = calculate_conserved_columns(alignment)

    assert len(conserved_columns) == 4
    assert [column["conserved"] for column in conserved_columns] == [
        True,
        True,
        False,
        True,
    ]

def test_msa_output_can_generate_conservation_summary():
    sequences = [
        "MKT",
        "MKTT",
        "MKT",
    ]

    alignment = align_sequences(sequences)

    summary = calculate_conservation_summary(alignment)

    assert summary.sequence_count == 3
    assert summary.alignment_length == 4
    assert summary.conserved_positions == 3
    assert summary.conservation_percentage == 75.0
    assert summary.mean_identity == 100.0

def test_align_sequences_handles_multiple_insertions_at_same_position():
    sequences = [
        "MKT",
        "MKTTT",
        "MKT",
    ]

    result = align_sequences(sequences)

    assert result == [
        "MK--T",
        "MKTTT",
        "MK--T",
    ]

def test_align_sequences_handles_deletion():
    sequences = [
        "MKT",
        "MK",
        "MKT",
    ]

    result = align_sequences(sequences)

    assert result == [
        "MKT",
        "MK-",
        "MKT",
    ]