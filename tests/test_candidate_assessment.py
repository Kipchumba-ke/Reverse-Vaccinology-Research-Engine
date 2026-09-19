from app.analysis.candidate_assessment import assess_candidate
from app.analysis.pipeline import analyze_protein
from app.analysis.host_similarity import (
    create_host_similarity_evidence,
)
from app.analysis.localization import (
    create_localization_evidence,
)
from app.analysis.essentiality import create_essentiality_evidence
import pytest

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
        "Strongest reported host match: 45.0% identity, "
        "query coverage=80.0%, subject coverage=75.0%, "
        "E-value=1e-10."
        in assessment.concerns
    )

def test_candidate_assessment_reports_strongest_host_match():
    first_match = create_host_similarity_evidence(
        target_id="pathogen_protein_1",
        host_id="human_protein_1",
        similarity_method="BLASTP",
        identity_percentage=95.0,
        alignment_length=20,
        query_coverage_percentage=5.0,
        subject_coverage_percentage=4.0,
        e_value=1e-50,
        source="Example database",
        confidence="medium",
        description="Short high-identity match.",
    )

    second_match = create_host_similarity_evidence(
        target_id="pathogen_protein_1",
        host_id="human_protein_2",
        similarity_method="BLASTP",
        identity_percentage=70.0,
        alignment_length=900,
        query_coverage_percentage=90.0,
        subject_coverage_percentage=85.0,
        e_value=1e-20,
        source="Example database",
        confidence="high",
        description="Broad host similarity match.",
    )

    result = analyze_protein(
        "MKTIIALSYIFCLVFAD",
        host_similarity_evidence=[
            first_match,
            second_match,
        ],
    )

    assessment = assess_candidate(result)

    assert (
        "Strongest reported host match: 70.0% identity, "
        "query coverage=90.0%, subject coverage=85.0%, "
        "E-value=1e-20."
        in assessment.concerns
    )

def test_candidate_assessment_rejects_missing_conservation_percentage():
    result = analyze_protein("MKTIIALSYIFCLVFAD")

    with pytest.raises(
        ValueError,
        match="conservation_percentage",
    ):
        assess_candidate(
            result,
            conservation_summary={},
        )


def test_candidate_assessment_rejects_invalid_conservation_percentage():
    result = analyze_protein("MKTIIALSYIFCLVFAD")

    with pytest.raises(
        ValueError,
        match="between 0 and 100",
    ):
        assess_candidate(
            result,
            conservation_summary={
                "conservation_percentage": 120.0,
            },
        )


def test_candidate_assessment_rejects_non_numeric_conservation_percentage():
    result = analyze_protein("MKTIIALSYIFCLVFAD")

    with pytest.raises(
        ValueError,
        match="must be numeric",
    ):
        assess_candidate(
            result,
            conservation_summary={
                "conservation_percentage": "high",
            },
        )

def test_candidate_assessment_treats_zero_conservation_as_limited():
    result = analyze_protein("MKTIIALSYIFCLVFAD")

    assessment = assess_candidate(
        result,
        conservation_summary={"conservation_percentage": 0.0},
    )

    assert (
        "limited exact conservation"
        in assessment.concerns[0].lower()
    )


def test_candidate_assessment_treats_fifty_percent_as_supporting():
    result = analyze_protein("MKTIIALSYIFCLVFAD")

    assessment = assess_candidate(
        result,
        conservation_summary={"conservation_percentage": 50.0},
    )

    assert (
        "conserved positions"
        in assessment.supporting_evidence[0].lower()
    )


def test_candidate_assessment_treats_one_hundred_percent_as_supporting():
    result = analyze_protein("MKTIIALSYIFCLVFAD")

    assessment = assess_candidate(
        result,
        conservation_summary={"conservation_percentage": 100.0},
    )

    assert (
        "conserved positions"
        in assessment.supporting_evidence[0].lower()
    )

def test_candidate_assessment_treats_values_below_fifty_as_limited():
    result = analyze_protein("MKTIIALSYIFCLVFAD")

    assessment = assess_candidate(
        result,
        conservation_summary={"conservation_percentage": 49.9},
    )

    assert (
        "limited exact conservation"
        in assessment.concerns[0].lower()
    )

def test_candidate_assessment_rejects_boolean_conservation_percentage():
    result = analyze_protein("MKTIIALSYIFCLVFAD")

    with pytest.raises(
        ValueError,
        match="must be numeric",
    ):
        assess_candidate(
            result,
            conservation_summary={
                "conservation_percentage": True
            },
        )

def test_candidate_assessment_describes_high_confidence_extracellular_localization():
    localization = create_localization_evidence(
        location="extracellular",
        source="PredictionTool",
        confidence="high",
        description="Predicted extracellular localization.",
    )

    result = analyze_protein(
        "MKTIIALSYIFCLVFAD",
        localization_evidence=[localization],
    )

    assessment = assess_candidate(result)

    assert any(
        "extracellular" in evidence.lower()
        for evidence in assessment.supporting_evidence
    )

def test_candidate_assessment_preserves_localization_confidence():
    localization = create_localization_evidence(
        location="outer_membrane",
        source="PredictionTool",
        confidence="medium",
        description="Predicted outer-membrane localization.",
    )

    result = analyze_protein(
        "MKTIIALSYIFCLVFAD",
        localization_evidence=[localization],
    )

    assessment = assess_candidate(result)

    assert any(
        "medium" in evidence.lower()
        for evidence in assessment.supporting_evidence
    )

def test_candidate_assessment_reports_unknown_localization():
    localization = create_localization_evidence(
        location="unknown",
        source="PredictionTool",
        confidence="low",
        description="Localization could not be confidently assigned.",
    )

    result = analyze_protein(
        "MKTIIALSYIFCLVFAD",
        localization_evidence=[localization],
    )

    assessment = assess_candidate(result)

    assert any(
        "unknown" in evidence.lower()
        for evidence in assessment.concerns
    )

def test_candidate_assessment_records_multiple_localization_predictions():
    extracellular = create_localization_evidence(
        location="extracellular",
        source="PredictorA",
        confidence="high",
        description="Predicted extracellular localization.",
    )

    outer_membrane = create_localization_evidence(
        location="outer_membrane",
        source="PredictorB",
        confidence="medium",
        description="Predicted outer-membrane localization.",
    )

    result = analyze_protein(
        "MKTIIALSYIFCLVFAD",
        localization_evidence=[
            extracellular,
            outer_membrane,
        ],
    )

    assessment = assess_candidate(result)

    assert (
        "Localization evidence has been supplied."
        in assessment.supporting_evidence
    )

    assert any(
        "extracellular" in evidence.lower()
        and "high" in evidence.lower()
        and "PredictorA" in evidence
        for evidence in assessment.supporting_evidence
    )

    assert any(
        "outer_membrane" in evidence.lower()
        and "medium" in evidence.lower()
        and "PredictorB" in evidence
        for evidence in assessment.supporting_evidence
    )

def test_candidate_assessment_reports_conflicting_localization_predictions():
    extracellular = create_localization_evidence(
        location="extracellular",
        source="PredictorA",
        confidence="high",
        description="Predicted extracellular localization.",
    )

    cytoplasm = create_localization_evidence(
        location="cytoplasm",
        source="PredictorB",
        confidence="high",
        description="Predicted cytoplasmic localization.",
    )

    result = analyze_protein(
        "MKTIIALSYIFCLVFAD",
        localization_evidence=[
            extracellular,
            cytoplasm,
        ],
    )

    assessment = assess_candidate(result)

    assert any(
        "conflicting localization" in evidence.lower()
        for evidence in assessment.concerns
    )

def test_candidate_assessment_does_not_report_conflict_for_agreeing_predictions():
    predictor_a = create_localization_evidence(
        location="outer_membrane",
        source="PredictorA",
        confidence="high",
        description="Predicted outer-membrane localization.",
    )

    predictor_b = create_localization_evidence(
        location="outer_membrane",
        source="PredictorB",
        confidence="medium",
        description="Predicted outer-membrane localization.",
    )

    result = analyze_protein(
        "MKTIIALSYIFCLVFAD",
        localization_evidence=[
            predictor_a,
            predictor_b,
        ],
    )

    assessment = assess_candidate(result)

    assert not any(
        "conflicting localization" in evidence.lower()
        for evidence in assessment.concerns
    )

def test_candidate_assessment_preserves_localization_description():
    localization = create_localization_evidence(
        location="extracellular",
        source="PredictionTool",
        confidence="high",
        description=(
            "Signal peptide detected; predicted "
            "extracellular localization."
        ),
    )

    result = analyze_protein(
        "MKTIIALSYIFCLVFAD",
        localization_evidence=[localization],
    )

    assessment = assess_candidate(result)

    assert any(
        "Signal peptide detected" in evidence
        for evidence in assessment.supporting_evidence
    )

def test_candidate_assessment_describes_essentiality_evidence():
    essentiality = create_essentiality_evidence(
        gene_id="geneA",
        organism="Example bacterium",
        essentiality_status="essential",
        source="Knockout study",
        confidence="high",
        description="Gene is essential for bacterial growth.",
    )

    result = analyze_protein(
        "MKTIIALSYIFCLVFAD",
        essentiality_evidence=[essentiality],
    )

    assessment = assess_candidate(result)

    assert (
        "Essentiality evidence has been supplied."
        in assessment.supporting_evidence
    )

    assert any(
        "essential" in evidence.lower()
        and "geneA" in evidence
        and "Example bacterium" in evidence
        and "high" in evidence.lower()
        for evidence in assessment.supporting_evidence
    )

@pytest.mark.parametrize(
    "essentiality_status",
    [
        "non-essential",
        "conditionally_essential",
    ],
)
def test_candidate_assessment_reports_essentiality_status(
    essentiality_status,
):
    essentiality = create_essentiality_evidence(
        gene_id="geneA",
        organism="Example bacterium",
        essentiality_status=essentiality_status,
        source="Essentiality database",
        confidence="medium",
        description="External essentiality evidence.",
    )

    result = analyze_protein(
        "MKTIIALSYIFCLVFAD",
        essentiality_evidence=[essentiality],
    )

    assessment = assess_candidate(result)

    assert any(
        essentiality_status in evidence
        for evidence in assessment.supporting_evidence
    )

def test_candidate_assessment_reports_unknown_essentiality():
    essentiality = create_essentiality_evidence(
        gene_id="geneA",
        organism="Example bacterium",
        essentiality_status="unknown",
        source="Essentiality database",
        confidence="low",
        description="Essentiality could not be established.",
    )

    result = analyze_protein(
        "MKTIIALSYIFCLVFAD",
        essentiality_evidence=[essentiality],
    )

    assessment = assess_candidate(result)

    assert any(
        "unknown" in evidence.lower()
        for evidence in assessment.concerns
    )

def test_candidate_assessment_records_multiple_essentiality_evidence():
    essential = create_essentiality_evidence(
        gene_id="geneA",
        organism="Organism A",
        essentiality_status="essential",
        source="Study A",
        confidence="high",
        description="Gene required for growth.",
    )

    conditional = create_essentiality_evidence(
        gene_id="geneA",
        organism="Organism A",
        essentiality_status="conditionally_essential",
        source="Study B",
        confidence="medium",
        description="Gene required under specific conditions.",
    )

    result = analyze_protein(
        "MKTIIALSYIFCLVFAD",
        essentiality_evidence=[
            essential,
            conditional,
        ],
    )

    assessment = assess_candidate(result)

    assert any(
        "essential" in evidence.lower()
        and "Study A" in evidence
        for evidence in assessment.supporting_evidence
    )

    assert any(
        "conditionally_essential" in evidence
        and "Study B" in evidence
        for evidence in assessment.supporting_evidence
    )

def test_candidate_assessment_identifies_broad_host_similarity():
    host_match = create_host_similarity_evidence(
        target_id="candidate_protein",
        host_id="human_protein",
        similarity_method="BLASTP",
        identity_percentage=72.0,
        alignment_length=320,
        query_coverage_percentage=96.0,
        subject_coverage_percentage=94.0,
        e_value=1e-40,
        source="BLASTP",
        confidence="high",
        description="Strong broad host-protein similarity.",
    )

    result = analyze_protein(
        "MKTIIALSYIFCLVFAD",
        host_similarity_evidence=[host_match],
    )

    assessment = assess_candidate(result)

    assert any(
        "broad" in evidence.lower()
        for evidence in assessment.concerns
    )

def test_candidate_assessment_distinguishes_partial_host_similarity():
    host_match = create_host_similarity_evidence(
        target_id="candidate_protein",
        host_id="human_protein",
        similarity_method="BLASTP",
        identity_percentage=85.0,
        alignment_length=90,
        query_coverage_percentage=22.0,
        subject_coverage_percentage=18.0,
        e_value=1e-25,
        source="BLASTP",
        confidence="high",
        description="High identity in a limited aligned region.",
    )

    result = analyze_protein(
        "MKTIIALSYIFCLVFAD",
        host_similarity_evidence=[host_match],
    )

    assessment = assess_candidate(result)

    assert any(
        "partial" in evidence.lower()
        for evidence in assessment.concerns
    )

def test_candidate_assessment_identifies_moderate_host_similarity():
    host_match = create_host_similarity_evidence(
        target_id="candidate_protein",
        host_id="human_protein",
        similarity_method="BLASTP",
        identity_percentage=45.0,
        alignment_length=210,
        query_coverage_percentage=70.0,
        subject_coverage_percentage=65.0,
        e_value=1e-8,
        source="BLASTP",
        confidence="medium",
        description="Moderate sequence similarity to a host protein.",
    )

    result = analyze_protein(
        "MKTIIALSYIFCLVFAD",
        host_similarity_evidence=[host_match],
    )

    assessment = assess_candidate(result)

    assert any(
        "moderate" in evidence.lower()
        for evidence in assessment.concerns
    )

def test_candidate_assessment_low_host_similarity_does_not_claim_safety():
    host_match = create_host_similarity_evidence(
        target_id="candidate_protein",
        host_id="human_protein",
        similarity_method="BLASTP",
        identity_percentage=12.0,
        alignment_length=180,
        query_coverage_percentage=60.0,
        subject_coverage_percentage=55.0,
        e_value=0.01,
        source="BLASTP",
        confidence="low",
        description="Relatively low sequence similarity to a host protein.",
    )

    result = analyze_protein(
        "MKTIIALSYIFCLVFAD",
        host_similarity_evidence=[host_match],
    )

    assessment = assess_candidate(result)

    assert any(
        "relatively low sequence similarity" in evidence.lower()
        for evidence in assessment.concerns
    )

    assert not any(
        "safe" in evidence.lower()
        for evidence in assessment.supporting_evidence
        + assessment.concerns
    )

def test_candidate_assessment_identifies_asymmetric_host_similarity():
    host_match = create_host_similarity_evidence(
        target_id="candidate_protein",
        host_id="human_protein",
        similarity_method="BLASTP",
        identity_percentage=82.0,
        alignment_length=180,
        query_coverage_percentage=92.0,
        subject_coverage_percentage=35.0,
        e_value=1e-25,
        source="BLASTP",
        confidence="high",
        description=(
            "High identity with asymmetric sequence coverage."
        ),
    )

    result = analyze_protein(
        "MKTIIALSYIFCLVFAD",
        host_similarity_evidence=[host_match],
    )

    assessment = assess_candidate(result)

    assert any(
        "asymmetric" in evidence.lower()
        for evidence in assessment.concerns
    )

def test_candidate_assessment_reports_broadest_host_match():
    broad_match = create_host_similarity_evidence(
        target_id="candidate_protein",
        host_id="host_protein_broad",
        similarity_method="BLASTP",
        identity_percentage=55.0,
        alignment_length=300,
        query_coverage_percentage=95.0,
        subject_coverage_percentage=90.0,
        e_value=1e-10,
        source="BLASTP",
        confidence="medium",
        description="Broad host-protein match.",
    )

    high_identity_match = create_host_similarity_evidence(
        target_id="candidate_protein",
        host_id="host_protein_local",
        similarity_method="BLASTP",
        identity_percentage=90.0,
        alignment_length=100,
        query_coverage_percentage=70.0,
        subject_coverage_percentage=70.0,
        e_value=1e-30,
        source="BLASTP",
        confidence="high",
        description="High identity but narrower match.",
    )

    result = analyze_protein(
        "MKTIIALSYIFCLVFAD",
        host_similarity_evidence=[
            broad_match,
            high_identity_match,
        ],
    )

    assessment = assess_candidate(result)

    assert any(
        "55.0% identity" in evidence
        and "query coverage=95.0%" in evidence
        for evidence in assessment.concerns
    )

def test_candidate_assessment_reports_high_identity_host_match():
    broad_match = create_host_similarity_evidence(
        target_id="candidate_protein",
        host_id="host_protein_broad",
        similarity_method="BLASTP",
        identity_percentage=55.0,
        alignment_length=300,
        query_coverage_percentage=95.0,
        subject_coverage_percentage=90.0,
        e_value=1e-10,
        source="BLASTP",
        confidence="medium",
        description="Broad host-protein match.",
    )

    high_identity_match = create_host_similarity_evidence(
        target_id="candidate_protein",
        host_id="host_protein_identity",
        similarity_method="BLASTP",
        identity_percentage=90.0,
        alignment_length=100,
        query_coverage_percentage=70.0,
        subject_coverage_percentage=70.0,
        e_value=1e-30,
        source="BLASTP",
        confidence="high",
        description="High identity host-protein match.",
    )

    result = analyze_protein(
        "MKTIIALSYIFCLVFAD",
        host_similarity_evidence=[
            broad_match,
            high_identity_match,
        ],
    )

    assessment = assess_candidate(result)

    assert any(
        "90.0% identity" in evidence
        for evidence in assessment.concerns
    )

def test_candidate_assessment_reports_localization_finding():
    localization = create_localization_evidence(
        location="extracellular",
        source="Example prediction tool",
        confidence="high",
        description="Protein is predicted to be extracellular.",
    )

    result = analyze_protein(
        "MKTIIALSYIFCLVFAD",
        localization_evidence=[localization],
    )

    assessment = assess_candidate(result)

    assert any(
        "Predicted localization: extracellular." in evidence
        for evidence in assessment.supporting_evidence
    )

def test_candidate_assessment_reports_agreeing_localization_predictions():
    extracellular_a = create_localization_evidence(
        location="extracellular",
        source="PredictorA",
        confidence="high",
        description="Predicted extracellular localization.",
    )

    extracellular_b = create_localization_evidence(
        location="extracellular",
        source="PredictorB",
        confidence="medium",
        description="Predicted extracellular localization.",
    )

    result = analyze_protein(
        "MKTIIALSYIFCLVFAD",
        localization_evidence=[
            extracellular_a,
            extracellular_b,
        ],
    )

    assessment = assess_candidate(result)

    assert any(
        "multiple localization predictions agree" in evidence.lower()
        for evidence in assessment.supporting_evidence
    )

def test_candidate_assessment_reports_essentiality_finding():
    essentiality = create_essentiality_evidence(
        gene_id="gene-123",
        organism="Example organism",
        essentiality_status="essential",
        source="Example essentiality database",
        confidence="high",
        description="Gene is essential for survival under the tested conditions.",
    )

    result = analyze_protein(
        "MKTIIALSYIFCLVFAD",
        essentiality_evidence=[essentiality],
    )

    assessment = assess_candidate(result)

    assert any(
        "Essentiality status: essential"
        in evidence
        for evidence in assessment.supporting_evidence
    )

def test_candidate_assessment_reports_agreeing_essentiality_evidence():
    essentiality_a = create_essentiality_evidence(
        gene_id="gene-123",
        organism="Example organism",
        essentiality_status="essential",
        source="DatabaseA",
        confidence="high",
        description="Gene is essential.",
    )

    essentiality_b = create_essentiality_evidence(
        gene_id="gene-123",
        organism="Example organism",
        essentiality_status="essential",
        source="DatabaseB",
        confidence="medium",
        description="Gene is required for survival.",
    )

    result = analyze_protein(
        "MKTIIALSYIFCLVFAD",
        essentiality_evidence=[
            essentiality_a,
            essentiality_b,
        ],
    )

    assessment = assess_candidate(result)

    assert any(
        "multiple essentiality records agree on the same status"
        in evidence.lower()
        for evidence in assessment.supporting_evidence
    )

def test_candidate_assessment_reports_conflicting_essentiality_evidence():
    essentiality_a = create_essentiality_evidence(
        gene_id="gene-123",
        organism="Example organism",
        essentiality_status="essential",
        source="DatabaseA",
        confidence="high",
        description="Gene is essential.",
    )

    essentiality_b = create_essentiality_evidence(
        gene_id="gene-123",
        organism="Example organism",
        essentiality_status="non-essential",
        source="DatabaseB",
        confidence="medium",
        description="Gene is not essential under the tested conditions.",
    )

    result = analyze_protein(
        "MKTIIALSYIFCLVFAD",
        essentiality_evidence=[
            essentiality_a,
            essentiality_b,
        ],
    )

    assessment = assess_candidate(result)

    assert any(
        "conflicting essentiality evidence"
        in evidence.lower()
        for evidence in assessment.concerns
    )

def test_candidate_assessment_reports_multiple_host_similarity_records():
    first_match = create_host_similarity_evidence(
        target_id="target-1",
        host_id="host-1",
        similarity_method="BLASTP",
        identity_percentage=45.0,
        alignment_length=200,
        query_coverage_percentage=80.0,
        subject_coverage_percentage=75.0,
        e_value=1e-10,
        source="DatabaseA",
        confidence="medium",
        description="Host similarity detected.",
    )

    second_match = create_host_similarity_evidence(
        target_id="target-1",
        host_id="host-2",
        similarity_method="BLASTP",
        identity_percentage=38.0,
        alignment_length=180,
        query_coverage_percentage=70.0,
        subject_coverage_percentage=65.0,
        e_value=1e-8,
        source="DatabaseB",
        confidence="medium",
        description="Another host similarity detected.",
    )

    result = analyze_protein(
        "MKTIIALSYIFCLVFAD",
        host_similarity_evidence=[
            first_match,
            second_match,
        ],
    )

    assessment = assess_candidate(result)

    assert any(
        "2 host-protein similarity records were supplied"
        in evidence
        for evidence in assessment.concerns
    )