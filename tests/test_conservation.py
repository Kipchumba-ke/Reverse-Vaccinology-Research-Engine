import pytest

from app.analysis.conservation import (
    calculate_pairwise_identity,
    calculate_conserved_columns,
    calculate_conservation_summary,
    find_conserved_regions,
)


def test_identical_sequences_have_100_percent_identity():
    result = calculate_pairwise_identity(
        "MKTIIALS",
        "MKTIIALS",
    )

    assert result == 100.0


def test_pairwise_identity():
    result = calculate_pairwise_identity(
        "MKTIIALS",
        "MKTIVALS",
    )

    assert result == pytest.approx(87.5)


def test_completely_different_sequences():
    result = calculate_pairwise_identity(
        "AAAA",
        "DDDD",
    )

    assert result == 0.0


def test_empty_sequence_is_rejected():
    with pytest.raises(ValueError):
        calculate_pairwise_identity(
            "",
            "AAAA",
        )


def test_different_lengths_are_rejected():
    with pytest.raises(ValueError):
        calculate_pairwise_identity(
            "AAAA",
            "AAA",
        )

def test_conserved_columns_are_identified():
    sequences = [
        "MKTIIALS",
        "MKTIVALS",
        "MKTIIALS",
        "MKTILALS",
    ]

    result = calculate_conserved_columns(sequences)

    assert result[0]["conserved"] is True
    assert result[0]["consensus"] == "M"

    assert result[4]["conserved"] is False
    assert result[4]["consensus"] == "I"
    assert result[4]["conservation_percentage"] == 50.0


def test_conserved_column_contains_amino_acids():
    sequences = [
        "MKTIIALS",
        "MKTIIALS",
    ]

    result = calculate_conserved_columns(sequences)

    assert result[0]["amino_acids"] == ["M", "M"]
    assert result[4]["amino_acids"] == ["I", "I"]


def test_all_columns_are_conserved():
    sequences = [
        "MKTIIALS",
        "MKTIIALS",
        "MKTIIALS",
    ]

    result = calculate_conserved_columns(sequences)

    assert all(
        column["conserved"]
        for column in result
    )


def test_variable_columns_are_detected():
    sequences = [
        "AAAA",
        "AATA",
        "AAGA",
    ]

    result = calculate_conserved_columns(sequences)

    assert result[0]["conserved"] is True
    assert result[1]["conserved"] is True
    assert result[2]["conserved"] is False
    assert result[3]["conserved"] is True


def test_empty_sequence_list_is_rejected():
    with pytest.raises(ValueError):
        calculate_conserved_columns([])


def test_empty_sequence_is_rejected():
    with pytest.raises(ValueError):
        calculate_conserved_columns([
            "MKTIIALS",
            "",
        ])


def test_different_alignment_lengths_are_rejected():
    with pytest.raises(ValueError):
        calculate_conserved_columns([
            "MKTIIALS",
            "MKTIIAL",
        ])

def test_conservation_summary():
    sequences = [
        "MKTIIALS",
        "MKTIVALS",
        "MKTIIALS",
        "MKTILALS",
    ]

    result = calculate_conservation_summary(sequences)

    assert result.sequence_count == 4
    assert result.alignment_length == 8
    assert result.conserved_positions == 7
    assert result.conservation_percentage == 87.5

def test_conservation_summary_to_dict():
    sequences = [
        "MKTIIALS",
        "MKTIIALS",
    ]

    result = calculate_conservation_summary(sequences)

    data = result.to_dict()

    assert data == {
        "sequence_count": 2,
        "alignment_length": 8,
        "mean_identity": 100.0,
        "conserved_positions": 8,
        "conservation_percentage": 100.0,
    }

def test_single_sequence_has_100_percent_mean_identity():
    result = calculate_conservation_summary([
        "MKTIIALS",
    ])

    assert result.sequence_count == 1
    assert result.mean_identity == 100.0
    assert result.conservation_percentage == 100.0

def test_conservation_summary_rejects_empty_input():
    with pytest.raises(ValueError):
        calculate_conservation_summary([])


def test_conservation_summary_rejects_different_lengths():
    with pytest.raises(ValueError):
        calculate_conservation_summary([
            "MKTIIALS",
            "MKTIIAL",
        ])

def test_conservation_percentage_is_calculated():
    sequences = [
        "MKTIIALS",
        "MKTIVALS",
        "MKTIIALS",
        "MKTILALS",
    ]

    result = calculate_conserved_columns(sequences)

    assert result[0]["conservation_percentage"] == 100.0
    assert result[4]["conservation_percentage"] == 50.0

def test_consensus_is_most_frequent_amino_acid():
    sequences = [
        "AAAA",
        "AATA",
        "AAGA",
    ]

    result = calculate_conserved_columns(sequences)

    assert result[2]["consensus"] == "A"
    assert result[2]["conservation_percentage"] == pytest.approx(
        33.33333333333333
    )

def test_conserved_regions_are_identified():
    sequences = [
        "MKTIIALS",
        "MKTIVALS",
        "MKTIIALS",
        "MKTILALS",
    ]

    columns = calculate_conserved_columns(sequences)

    regions = find_conserved_regions(columns)

    assert regions == [
        {
            "start": 1,
            "end": 4,
            "length": 4,
            "consensus" : "MKTI",
        },
        {
            "start": 6,
            "end": 8,
            "length": 3,
            "consensus": "ALS",
        },
    ]

def test_all_conserved_positions_form_one_region():
    sequences = [
        "MKTIIALS",
        "MKTIIALS",
        "MKTIIALS",
    ]

    columns = calculate_conserved_columns(sequences)

    regions = find_conserved_regions(columns)

    assert regions == [
        {
            "start": 1,
            "end": 8,
            "length": 8,
            "consensus": "MKTIIALS",
        }
    ]

def test_no_conserved_positions_returns_empty_list():
    sequences = [
        "AAAA",
        "DDDD",
    ]

    columns = calculate_conserved_columns(sequences)

    regions = find_conserved_regions(columns)

    assert regions == []

def test_minimum_region_length_filters_short_regions():
    sequences = [
        "MKTIIALS",
        "MKTIVALS",
        "MKTIIALS",
        "MKTILALS",
    ]

    columns = calculate_conserved_columns(sequences)

    regions = find_conserved_regions(
        columns,
        min_length=4,
    )

    assert regions == [
        {
            "start": 1,
            "end": 4,
            "length": 4,
            "consensus": "MKTI",
        }
    ]

def test_invalid_minimum_region_length_is_rejected():
    with pytest.raises(ValueError):
        find_conserved_regions(
            [],
            min_length=0,
        )

def test_pairwise_identity_ignores_gap_positions():
    result = calculate_pairwise_identity(
        "MKTIIALS",
        "MKT-IALS",
    )

    assert result == pytest.approx(100.0)

def test_pairwise_identity_rejects_only_gap_comparison():
    with pytest.raises(ValueError):
        calculate_pairwise_identity(
            "----",
            "----",
        )

def test_gap_information_is_recorded():
    sequences = [
        "MKTIIALS",
        "MKT-IALS",
        "MKTIIALS",
        "MKTIIALS",
    ]

    result = calculate_conserved_columns(sequences)

    gap_column = result[3]

    assert gap_column["gap_count"] == 1
    assert gap_column["gap_percentage"] == 25.0

def test_gap_prevents_full_conservation():
    sequences = [
        "MKTIIALS",
        "MKT-IALS",
        "MKTIIALS",
        "MKTIIALS",
    ]

    result = calculate_conserved_columns(sequences)

    gap_column = result[3]

    assert gap_column["conserved"] is False

def test_consensus_ignores_gaps():
    sequences = [
        "MKTIIALS",
        "MKT-IALS",
        "MKTIIALS",
        "MKTIIALS",
    ]

    result = calculate_conserved_columns(sequences)

    gap_column = result[3]

    assert gap_column["consensus"] == "I"
    assert gap_column["conservation_percentage"] == 100.0

def test_entirely_gapped_column_has_no_consensus():
    sequences = [
        "MKT-",
        "MKT-",
        "MKT-",
    ]

    result = calculate_conserved_columns(sequences)

    gap_column = result[3]

    assert gap_column["consensus"] is None
    assert gap_column["conservation_percentage"] == 0.0
    assert gap_column["gap_percentage"] == 100.0
    assert gap_column["conserved"] is False

def test_conserved_regions_include_consensus_sequence():
    columns = [
        {
            "position": 1,
            "amino_acids": ["M", "M", "M"],
            "consensus": "M",
            "conserved": True,
            "conservation_percentage": 100.0,
            "gap_count": 0,
            "gap_percentage": 0.0,
        },
        {
            "position": 2,
            "amino_acids": ["K", "K", "K"],
            "consensus": "K",
            "conserved": True,
            "conservation_percentage": 100.0,
            "gap_count": 0,
            "gap_percentage": 0.0,
        },
        {
            "position": 3,
            "amino_acids": ["T", "T", "T"],
            "consensus": "T",
            "conserved": True,
            "conservation_percentage": 100.0,
            "gap_count": 0,
            "gap_percentage": 0.0,
        },
        {
            "position": 4,
            "amino_acids": ["A", "A", "G"],
            "consensus": "A",
            "conserved": False,
            "conservation_percentage": 66.7,
            "gap_count": 0,
            "gap_percentage": 0.0,
        },
    ]

    regions = find_conserved_regions(columns)

    assert regions == [
        {
            "start": 1,
            "end": 3,
            "length": 3,
            "consensus": "MKT",
        }
    ]