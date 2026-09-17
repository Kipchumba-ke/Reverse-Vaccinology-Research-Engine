from app.analysis.candidate_assessment import assess_candidate
from app.analysis.pipeline import analyze_protein
from app.analysis.host_similarity import (
    create_host_similarity_evidence,
)
from app.analysis.localization import (
    create_localization_evidence,
)
def test_candidate_assessment_reports_missing_evidence():
    result = analyze_protein("MKTIIALSYIFCLVFAD")

    assessment = assess_candidate(result)

    assert assessment.status == "requires_further_review"
    assert assessment.missing_evidence
    assert "Host-protein similarity analysis." in (
        assessment.missing_evidence
    )

def test_candidate_assessment_records_supplied_localization():
    localization = create_localization_evidence(
        location="extracellular",
        source="Example predictor",
        confidence="medium",
        description="Predicted extracellular localization.",
    )

    result = analyze_protein(
        "MKTIIALSYIFCLVFAD",
        localization_evidence=[localization],
    )

    assessment = assess_candidate(result)

    assert (
        "Localization evidence has been supplied."
        in assessment.supporting_evidence
    )

def test_candidate_assessment_records_host_similarity_concern():
    host_similarity = create_host_similarity_evidence(
        target_id="pathogen_protein_1",
        host_id="human_protein_1",
        similarity_method="BLASTP",
        identity_percentage=45.0,
        alignment_length=220,
        query_coverage_percentage=80.0,
        subject_coverage_percentage=75.0,
        e_value=1e-10,
        source="Example database",
        confidence="medium",
        description="Reported host similarity.",
    )

    result = analyze_protein(
        "MKTIIALSYIFCLVFAD",
        host_similarity_evidence=[host_similarity],
    )

    assessment = assess_candidate(result)

    assert assessment.status == "requires_further_review"
    assert (
        "Host-similarity evidence requires biological and "
        "alignment-level review."
        in assessment.concerns
    )