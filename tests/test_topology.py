from app.analysis.interpretation import (
    interpret_transmembrane_candidates,
    is_transmembrane_candidate,
)
from app.analysis.topology import (
    count_transmembrane_segments,
    flag_signal_peptide_overlap,
    infer_localization_hint,
)

SIGNAL_PEPTIDE = {"detected": True, "cleavage_after": 21}
NO_SIGNAL_PEPTIDE = {"detected": False, "cleavage_after": None}


def tm(start, end):
    return {
        "start": start,
        "end": end,
        "length": end - start + 1,
        "classification": "candidate_transmembrane",
    }


def test_region_inside_the_signal_peptide_is_reclassified():
    flagged = flag_signal_peptide_overlap([tm(6, 18)], SIGNAL_PEPTIDE)

    assert flagged[0]["overlaps_signal_peptide"] is True
    assert flagged[0]["revised_classification"] == "signal_peptide_h_region"
    assert flagged[0]["classification"] == "candidate_transmembrane"


def test_region_after_the_signal_peptide_keeps_its_classification():
    flagged = flag_signal_peptide_overlap([tm(60, 80)], SIGNAL_PEPTIDE)

    assert flagged[0]["overlaps_signal_peptide"] is False
    assert flagged[0]["revised_classification"] == "candidate_transmembrane"


def test_nothing_is_reclassified_without_a_signal_peptide():
    flagged = flag_signal_peptide_overlap([tm(6, 18)], NO_SIGNAL_PEPTIDE)

    assert flagged[0]["overlaps_signal_peptide"] is False
    assert flagged[0]["revised_classification"] == "candidate_transmembrane"


def test_input_candidates_are_not_modified():
    candidates = [tm(6, 18)]

    flag_signal_peptide_overlap(candidates, SIGNAL_PEPTIDE)

    assert "revised_classification" not in candidates[0]


def test_segments_overlapping_the_signal_peptide_are_not_counted():
    flagged = flag_signal_peptide_overlap(
        [tm(6, 18), tm(60, 80), tm(100, 120)], SIGNAL_PEPTIDE
    )

    assert count_transmembrane_segments(flagged) == 2


def test_hydrophobic_regions_are_not_counted_as_segments():
    region = {"start": 5, "end": 40, "classification": "hydrophobic_region"}

    assert count_transmembrane_segments([region]) == 0


def test_signal_peptide_without_segments_hints_secreted_or_periplasmic():
    hint = infer_localization_hint(SIGNAL_PEPTIDE, [])

    assert hint["hint"] == "secreted_or_periplasmic"
    assert hint["confidence"] == "low"


def test_transmembrane_segments_hint_membrane_association():
    hint = infer_localization_hint(NO_SIGNAL_PEPTIDE, [tm(10, 30)])

    assert hint["hint"] == "membrane_associated"


def test_signal_peptide_plus_segment_hints_membrane_association():
    hint = infer_localization_hint(SIGNAL_PEPTIDE, [tm(60, 80)])

    assert hint["hint"] == "membrane_associated"
    assert any("signal peptide" in line.lower() for line in hint["basis"])


def test_signal_peptide_core_alone_does_not_imply_membrane_association():
    flagged = flag_signal_peptide_overlap([tm(6, 18)], SIGNAL_PEPTIDE)

    assert infer_localization_hint(SIGNAL_PEPTIDE, flagged)["hint"] == (
        "secreted_or_periplasmic"
    )


def test_no_features_hint_is_unclassified_with_caveats():
    hint = infer_localization_hint(NO_SIGNAL_PEPTIDE, [])

    assert hint["hint"] == "cytoplasmic_or_unclassified"
    assert any("beta-barrel" in caveat for caveat in hint["caveats"])


def test_hint_is_marked_as_not_independent_evidence():
    hint = infer_localization_hint(NO_SIGNAL_PEPTIDE, [])

    assert hint["source"] == "ReverseVax topology heuristic"
    assert any("not independent" in caveat for caveat in hint["caveats"])


def test_interpretation_counts_only_real_transmembrane_candidates():
    candidates = [
        {"start": 5, "end": 40, "classification": "hydrophobic_region"},
        tm(60, 80),
    ]

    result = interpret_transmembrane_candidates(candidates)

    assert result.finding == "Transmembrane candidates: 1"
    assert "One region" in result.interpretation


def test_interpretation_excludes_signal_peptide_regions_and_says_so():
    flagged = flag_signal_peptide_overlap([tm(6, 18)], SIGNAL_PEPTIDE)

    result = interpret_transmembrane_candidates(flagged)

    assert result.finding == "Transmembrane candidates: 0"
    assert "signal peptide" in result.interpretation


def test_bare_coordinates_are_still_counted():
    assert is_transmembrane_candidate({"start": 10, "end": 30}) is True
    assert interpret_transmembrane_candidates(
        [{"start": 10, "end": 30}]
    ).finding == "Transmembrane candidates: 1"
