import pytest

from app.analysis.antigenicity import (
    PROPENSITY,
    annotate_peptides_with_antigenicity,
    calculate_propensity_profile,
    predict_antigenic_regions,
)


def test_scale_covers_the_twenty_amino_acids_and_is_centred_near_one():
    assert set(PROPENSITY) == set("ACDEFGHIKLMNPQRSTVWY")
    assert 0.95 < sum(PROPENSITY.values()) / 20 < 1.10


def test_most_and_least_antigenic_residues_match_the_published_scale():
    assert max(PROPENSITY, key=PROPENSITY.get) == "C"
    assert min(PROPENSITY, key=PROPENSITY.get) == "N"
    assert PROPENSITY["V"] > PROPENSITY["L"] > PROPENSITY["I"]


def test_profile_assigns_window_scores_to_the_central_residue():
    profile = calculate_propensity_profile("A" * 9, window=7)

    assert profile[:3] == [None, None, None]
    assert profile[-3:] == [None, None, None]
    assert profile[3:6] == [pytest.approx(PROPENSITY["A"])] * 3


def test_profile_rejects_even_windows():
    with pytest.raises(ValueError, match="odd"):
        calculate_propensity_profile("A" * 20, window=6)


def test_high_propensity_stretch_is_reported_and_low_stretch_is_not():
    sequence = "V" * 20 + "N" * 20

    result = predict_antigenic_regions(sequence)

    assert len(result["regions"]) == 1
    region = result["regions"][0]
    assert region["start"] >= 4
    assert region["end"] <= 20
    assert region["length"] >= 8
    assert set(region["sequence"]) == {"V"}
    # Windows at the edge of the stretch include a few low-propensity
    # residues, so the mean sits a little below the pure-V value.
    assert 1.30 < region["mean_propensity"] <= PROPENSITY["V"]


def test_regions_shorter_than_the_minimum_length_are_dropped():
    sequence = "N" * 15 + "VVVVVVVVV" + "N" * 15

    assert len(predict_antigenic_regions(sequence)["regions"]) == 1
    assert predict_antigenic_regions(
        sequence, min_region_length=20
    )["regions"] == []


def test_threshold_is_the_proteins_own_average():
    sequence = "VNVNVNVNVNVNVNVNVNVN"
    expected = sum(PROPENSITY[r] for r in sequence) / len(sequence)

    assert predict_antigenic_regions(sequence)["threshold"] == pytest.approx(
        expected, abs=1e-4
    )


def test_short_sequences_return_no_regions_with_a_note():
    result = predict_antigenic_regions("MKTAYI")

    assert result["regions"] == []
    assert any("shorter" in note for note in result["notes"])


def test_result_names_its_method_and_limits():
    result = predict_antigenic_regions("V" * 20 + "N" * 20)

    assert "Kolaskar" in result["method"]
    assert any("structure" in note for note in result["notes"])


def test_invalid_sequence_is_rejected():
    with pytest.raises(ValueError):
        predict_antigenic_regions("MKT*AYI")


def test_peptides_are_annotated_with_overlap_and_propensity():
    peptides = [
        {"start": 1, "end": 4, "sequence": "VVVV"},
        {"start": 30, "end": 33, "sequence": "NNNN"},
    ]
    regions = [{"start": 4, "end": 20}]

    annotated = annotate_peptides_with_antigenicity(peptides, regions)

    assert annotated[0]["overlaps_antigenic_region"] is True
    assert annotated[1]["overlaps_antigenic_region"] is False
    assert annotated[0]["mean_antigenic_propensity"] == pytest.approx(1.383)
    assert annotated[1]["mean_antigenic_propensity"] == pytest.approx(0.776)
    assert annotated[0]["sequence"] == "VVVV"
