import json

from app.analysis.pipeline import analyze_protein
from app.reporting.report import generate_protein_report

# Synthetic: short basic N-region, hydrophobic core, small-residue
# cleavage site (AXA), then a hydrophilic mature region.
SIGNAL_PEPTIDE_PROTEIN = (
    "MKKRLLLALLLALVLAAVSAQA"
    "DEKSTNQDEKSTNQDEKSTNQDEKSTNQ"
)
CYTOPLASMIC_PROTEIN = "MSDKEQRTNDEKSTQRDENKTSQRDEKSTNQ"


def test_result_carries_sequence_predictions():
    result = analyze_protein(SIGNAL_PEPTIDE_PROTEIN)

    assert set(result.sequence_predictions) == {
        "signal_peptide",
        "antigenic_regions",
        "localization_hint",
    }
    assert "detected" in result.sequence_predictions["signal_peptide"]
    assert "regions" in result.sequence_predictions["antigenic_regions"]
    assert (
        result.sequence_predictions["localization_hint"]["confidence"]
        == "low"
    )


def test_peptide_windows_are_annotated_with_antigenicity():
    result = analyze_protein(CYTOPLASMIC_PROTEIN)

    assert result.peptide_candidates
    for peptide in result.peptide_candidates:
        assert "mean_antigenic_propensity" in peptide
        assert isinstance(peptide["overlaps_antigenic_region"], bool)


def test_transmembrane_candidates_are_flagged_for_signal_overlap():
    result = analyze_protein(SIGNAL_PEPTIDE_PROTEIN)

    for candidate in result.transmembrane_candidates:
        assert "overlaps_signal_peptide" in candidate
        assert "revised_classification" in candidate


def test_localization_evidence_stays_empty_without_external_data():
    result = analyze_protein(SIGNAL_PEPTIDE_PROTEIN)

    assert result.localization_evidence == []
    assert result.to_dict()["localization_evidence"] == []


def test_similarity_is_computed_only_with_an_alignment():
    plain = analyze_protein(CYTOPLASMIC_PROTEIN)
    aligned = analyze_protein(
        CYTOPLASMIC_PROTEIN,
        aligned_sequences=[CYTOPLASMIC_PROTEIN, CYTOPLASMIC_PROTEIN],
    )

    assert plain.conservation_similarity is None
    assert aligned.conservation_similarity is not None


def test_report_surfaces_predictions_without_new_top_level_keys():
    report = generate_protein_report(
        analyze_protein(SIGNAL_PEPTIDE_PROTEIN)
    )

    assert set(report) == {
        "metadata",
        "protein",
        "measurements",
        "peptide_candidates",
        "conservation",
        "evidence",
        "interpretations",
        "candidate_assessment",
        "limitations",
    }
    assert "sequence_predictions" in report["measurements"]
    assert "similarity" in report["conservation"]
    assert any(
        "not B-cell or T-cell epitope prediction" in note
        for note in report["limitations"]
    )
    assert any(
        "provisional thresholds" in note for note in report["limitations"]
    )


def test_report_is_json_serialisable():
    report = generate_protein_report(
        analyze_protein(SIGNAL_PEPTIDE_PROTEIN)
    )

    json.dumps(report)


def test_host_threshold_overrides_change_interpretation(monkeypatch):
    from app.analysis.candidate_assessment import _interpret_host_similarity
    from app.models.host_similarity import HostSimilarityEvidence

    evidence = HostSimilarityEvidence(
        target_id="t", host_id="h", similarity_method="BLASTP",
        identity_percentage=75.0, alignment_length=100,
        query_coverage_percentage=95.0, subject_coverage_percentage=95.0,
        e_value=1e-10, source="test", confidence="high", description="d",
    )

    assert "Broad host-protein similarity" in _interpret_host_similarity(
        evidence
    )

    monkeypatch.setenv("HOST_SIMILARITY_BROAD_IDENTITY", "90")

    assert "Moderate" in _interpret_host_similarity(evidence)
