import pytest

from app.analysis.hydrophobicity import (calculate_gravy, calculate_hydropathy_profile, find_hydrophobic_regions, merge_hydrophobic_regions, summarize_hydrophobic_regions, classify_transmembrane_candidates)


def test_gravy_for_all_alanine():
    result = calculate_gravy("AAAA")

    assert result == pytest.approx(1.8)


def test_gravy_for_all_aspartic_acid():
    result = calculate_gravy("DDDD")

    assert result == pytest.approx(-3.5)


def test_gravy_for_mixed_sequence():
    result = calculate_gravy("AVIL")

    expected = (1.8 + 4.2 + 4.5 + 3.8) / 4

    assert result == pytest.approx(expected)


def test_gravy_is_rejected_for_empty_sequence():
    with pytest.raises(ValueError):
        calculate_gravy("")


def test_gravy_rejects_invalid_amino_acids():
    with pytest.raises(ValueError):
        calculate_gravy("MKT!")


def test_hydropathy_profile_has_correct_number_of_windows():
    result = calculate_hydropathy_profile(
        "AAAAAA",
        window_size=3,
    )

    assert len(result) == 4

def test_hydropathy_profile_positions():
    result = calculate_hydropathy_profile(
        "AAAAAA",
        window_size=3,
    )

    assert result[0]["start"] == 1
    assert result[0]["end"] == 3

    assert result[-1]["start"] == 4
    assert result[-1]["end"] == 6

def test_hydropathy_profile_average():
    result = calculate_hydropathy_profile(
        "AAAA",
        window_size=2,
    )

    assert result[0]["hydropathy"] == pytest.approx(1.8)
    assert result[1]["hydropathy"] == pytest.approx(1.8)
    assert result[2]["hydropathy"] == pytest.approx(1.8)

def test_hydropathy_profile_rejects_invalid_window():
    with pytest.raises(ValueError):
        calculate_hydropathy_profile(
            "AAAA",
            window_size=0,
        )


def test_hydropathy_profile_rejects_window_larger_than_sequence():
    with pytest.raises(ValueError):
        calculate_hydropathy_profile(
            "AAAA",
            window_size=5,
        )

def test_find_hydrophobic_regions():
    result = find_hydrophobic_regions(
        "IIIIIIIIII",
        window_size=5,
        threshold=4.0,
    )

    assert len(result) == 6

def test_hydrophilic_sequence_has_no_hydrophobic_regions():
    result = find_hydrophobic_regions(
        "DDDDDDDDDD",
        window_size=5,
        threshold=1.6,
    )

    assert result == []

def test_hydrophobic_region_threshold_is_validated():
    with pytest.raises(ValueError):
        find_hydrophobic_regions(
            "AAAAAA",
            window_size=3,
            threshold=5.0,
        )

def test_overlapping_hydrophobic_regions_are_merged():
    regions = [
        {"start": 10, "end": 28},
        {"start": 11, "end": 29},
        {"start": 12, "end": 30},
    ]

    result = merge_hydrophobic_regions(regions)

    assert result == [
        {"start": 10, "end": 30}
    ]

def test_adjacent_hydrophobic_regions_are_merged():
    regions = [
        {"start": 10, "end": 20},
        {"start": 21, "end": 30},
    ]

    result = merge_hydrophobic_regions(regions)

    assert result == [
        {"start": 10, "end": 30}
    ]

def test_separate_hydrophobic_regions_remain_separate():
    regions = [
        {"start": 10, "end": 20},
        {"start": 30, "end": 40},
    ]

    result = merge_hydrophobic_regions(regions)

    assert result == [
        {"start": 10, "end": 20},
        {"start": 30, "end": 40},
    ]

def test_merging_empty_regions_returns_empty_list():
    result = merge_hydrophobic_regions([])

    assert result == []

def test_hydrophobic_region_summary():
    sequence = "AAAAIIII"

    regions = [
        {
            "start": 5,
            "end": 8,
        }
    ]

    result = summarize_hydrophobic_regions(
        sequence,
        regions,
    )

    assert result == [
        {
            "start": 5,
            "end": 8,
            "length": 4,
            "sequence": "IIII",
            "average_hydropathy": pytest.approx(4.5),
        }
    ]

def test_summarizing_empty_regions_returns_empty_list():
    result = summarize_hydrophobic_regions(
        "AAAA",
        [],
    )

    assert result == []

def test_region_coordinates_outside_sequence_are_rejected():
    with pytest.raises(ValueError):
        summarize_hydrophobic_regions(
            "AAAA",
            [{"start": 2, "end": 10}],
        )

def test_reversed_region_coordinates_are_rejected():
    with pytest.raises(ValueError):
        summarize_hydrophobic_regions(
            "AAAA",
            [{"start": 4, "end": 2}],
        )

def test_transmembrane_candidate_is_identified():
    regions = [
        {
            "start": 42,
            "end": 62,
            "length": 21,
            "sequence": "IIIIIIIIIIIIIIIIIIIII",
            "average_hydropathy": 4.5,
        }
    ]

    result = classify_transmembrane_candidates(regions)

    assert result[0]["classification"] == (
        "candidate_transmembrane"
    )

    assert result[0]["length_matches"] is True
    assert result[0]["hydropathy_matches"] is True

def test_short_hydrophobic_region_is_not_tm_candidate():
    regions = [
        {
            "start": 1,
            "end": 10,
            "length": 10,
            "sequence": "IIIIIIIIII",
            "average_hydropathy": 4.5,
        }
    ]

    result = classify_transmembrane_candidates(regions)

    assert result[0]["classification"] == (
        "hydrophobic_region"
    )
    assert result[0]["length_matches"] is False

def test_low_hydropathy_region_is_not_tm_candidate():
    regions = [
        {
            "start": 1,
            "end": 20,
            "length": 20,
            "sequence": "DEDEDEDEDEDEDEDEDEDE",
            "average_hydropathy": -3.5,
        }
    ]

    result = classify_transmembrane_candidates(regions)

    assert result[0]["classification"] == (
        "hydrophobic_region"
    )
    assert result[0]["hydropathy_matches"] is False

def test_tm_min_length_must_be_positive():
    with pytest.raises(ValueError):
        classify_transmembrane_candidates(
            [],
            min_length=0,
        )


def test_tm_max_length_cannot_be_smaller_than_min():
    with pytest.raises(ValueError):
        classify_transmembrane_candidates(
            [],
            min_length=25,
            max_length=18,
        )