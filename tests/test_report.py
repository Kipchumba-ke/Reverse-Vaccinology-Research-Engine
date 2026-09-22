from app.analysis.pipeline import analyze_protein
from app.analysis.essentiality import (
    create_essentiality_evidence,
)
from app.analysis.localization import (
    create_localization_evidence,
)
from app.reporting.report import generate_protein_report
from app.analysis.host_similarity import create_host_similarity_evidence


def test_generate_basic_report():
    result = analyze_protein(
        "MKTIIALSYIFCLVFAD"
    )

    report = generate_protein_report(result)

    assert "protein" in report
    assert "measurements" in report
    assert "evidence" in report
    assert "interpretations" in report
    assert "limitations" in report


def test_report_contains_external_evidence():
    localization = create_localization_evidence(
        location="outer_membrane",
        source="Prediction database",
        confidence="medium",
        description="Evidence supports outer membrane localization.",
    )

    essentiality = create_essentiality_evidence(
        gene_id="geneA",
        organism="Example bacterium",
        essentiality_status="essential",
        source="Knockout study",
        confidence="high",
        description="Gene disruption prevented viable growth.",
    )

    result = analyze_protein(
        "MKTIIALSYIFCLVFAD",
        localization_evidence=[localization],
        essentiality_evidence=[essentiality],
    )

    report = generate_protein_report(result)

    assert len(report["evidence"]["localization"]) == 1
    assert len(report["evidence"]["essentiality"]) == 1
    assert (
        report["evidence"]["essentiality"][0]
        ["essentiality_status"]
        == "essential"
    )


def test_report_accepts_conservation_data():
    result = analyze_protein(
        "MKTIIALSYIFCLVFAD"
    )

    conservation_summary = {
        "conservation_percentage": 85.0,
        "alignment_length": 17,
        "sequence_count": 3,
    }

    conserved_regions = [
        {
            "start": 2,
            "end": 8,
            "length": 7,
        }
    ]

    report = generate_protein_report(
        result,
        conservation_summary=conservation_summary,
        conserved_regions=conserved_regions,
    )

    assert (
        report["conservation"]["summary"]
        ["conservation_percentage"]
        == 85.0
    )

    assert len(report["conservation"]["regions"]) == 1

def test_report_contains_hydrophobicity_interpretation():
    result = analyze_protein("MKTIIALSYIFCLVFAD")

    report = generate_protein_report(result)

    hydrophobicity = next(
        item
        for item in report["interpretations"]
        if item["category"] == "hydrophobicity"
    )

    assert "GRAVY" in hydrophobicity["finding"]
    assert hydrophobicity["interpretation"]


def test_report_contains_transmembrane_interpretation():
    result = analyze_protein("MKTIIALSYIFCLVFAD")

    report = generate_protein_report(result)

    membrane = next(
        item
        for item in report["interpretations"]
        if item["category"] == "membrane_topology"
    )

    assert "Transmembrane candidates" in membrane["finding"]
    assert membrane["interpretation"]


def test_report_contains_conservation_interpretation():
    result = analyze_protein("MKTIIALSYIFCLVFAD")

    report = generate_protein_report(
        result,
        conservation_summary={
            "conservation_percentage": 90.0,
            "alignment_length": 17,
            "sequence_count": 4,
        },
    )

    conservation = next(
        item
        for item in report["interpretations"]
        if item["category"] == "conservation"
    )

    assert "90.0%" in conservation["finding"]
    assert "strong conservation" in conservation["interpretation"]

def test_report_contains_host_similarity_evidence():
    evidence = create_host_similarity_evidence(
        target_id="target_A",
        host_id="host_A",
        similarity_method="BLASTP",
        identity_percentage=12.0,
        alignment_length=100,
        query_coverage_percentage=80.0,
        subject_coverage_percentage=75.0,
        e_value=1.5,
        source="Database",
        confidence="low",
        description="Low similarity.",
    )

    result = analyze_protein(
        "MKTIIALSYIFCLVFAD",
        host_similarity_evidence=[evidence],
    )

    report = generate_protein_report(result)

    assert len(report["evidence"]["host_similarity"]) == 1
    assert (
        report["evidence"]["host_similarity"][0]["host_id"]
        == "host_A"
    )

def test_report_contains_host_similarity_interpretation():
    evidence = create_host_similarity_evidence(
        target_id="pathogen_protein_1",
        host_id="human_protein_1",
        similarity_method="BLASTP",
        identity_percentage=12.0,
        alignment_length=180,
        query_coverage_percentage=80.0,
        subject_coverage_percentage=75.0,
        e_value=0.01,
        source="Example database",
        confidence="medium",
        description="Low-identity match recorded for review.",
    )

    result = analyze_protein(
        "MKTIIALSYIFCLVFAD",
        host_similarity_evidence=[evidence],
    )

    report = generate_protein_report(result)

    categories = [
        item["category"]
        for item in report["interpretations"]
    ]

    assert "host_similarity" in categories

def test_report_contains_candidate_assessment():
    result = analyze_protein(
        "MKTIIALSYIFCLVFAD"
    )

    report = generate_protein_report(result)

    assessment = report["candidate_assessment"]

    assert assessment["status"] == "requires_further_review"
    assert isinstance(
        assessment["supporting_evidence"],
        list,
    )
    assert isinstance(
        assessment["concerns"],
        list,
    )
    assert isinstance(
        assessment["missing_evidence"],
        list,
    )

def test_report_contains_metadata():
    result = analyze_protein(
        "MKTIIALSYIFCLVFAD"
    )

    report = generate_protein_report(result)

    assert report["metadata"]["report_type"] == "reverse_vaccinology"
    assert report["metadata"]["report_version"] == "1.0"

def test_report_contains_analysis_pipeline_metadata():
    result = analyze_protein(
        "MKTIIALSYIFCLVFAD"
    )

    report = generate_protein_report(result)

    assert (
        report["metadata"]["analysis_pipeline"]
        == "protein_sequence_analysis"
    )

def test_report_contains_protein_id():
    result = analyze_protein(
        "MKTIIALSYIFCLVFAD",
        protein_id="protein_1",
    )

    report = generate_protein_report(result)

    assert report["protein"]["id"] == "protein_1"

def test_report_contains_localization_interpretation():
    localization = create_localization_evidence(
        location="outer_membrane",
        source="Prediction database",
        confidence="high",
        description="Evidence supports outer membrane localization.",
    )

    result = analyze_protein(
        "MKTIIALSYIFCLVFAD",
        localization_evidence=[localization],
    )

    report = generate_protein_report(result)

    localization_interpretation = next(
        item
        for item in report["interpretations"]
        if item["category"] == "localization"
    )

    assert "outer_membrane" in localization_interpretation["finding"]
    assert "outer membrane" in (
        localization_interpretation["interpretation"].lower()
    )

def test_report_contains_essentiality_interpretation():
    essentiality = create_essentiality_evidence(
        gene_id="geneA",
        organism="Example bacterium",
        essentiality_status="essential",
        source="Knockout study",
        confidence="high",
        description="Gene disruption prevented viable growth.",
    )

    result = analyze_protein(
        "MKTIIALSYIFCLVFAD",
        essentiality_evidence=[essentiality],
    )

    report = generate_protein_report(result)

    essentiality_interpretation = next(
        item
        for item in report["interpretations"]
        if item["category"] == "essentiality"
    )

    assert "essential" in essentiality_interpretation["finding"]
    assert "essential" in (
        essentiality_interpretation["interpretation"].lower()
    )

def test_report_contains_candidate_assessment_rationale():
    result = analyze_protein("MKTIIALSYIFCLVFAD")

    report = generate_protein_report(result)

    assert "rationale" in report["candidate_assessment"]
    assert "missing evidence" in (
        report["candidate_assessment"]["rationale"].lower()
    )