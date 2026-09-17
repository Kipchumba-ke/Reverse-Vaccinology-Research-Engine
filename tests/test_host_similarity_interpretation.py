from app.analysis.interpretation import interpret_host_similarity


def test_no_host_similarity_evidence():
    evidence = interpret_host_similarity([])

    assert evidence.category == "host_similarity"
    assert evidence.confidence == "low"
    assert "No host-similarity evidence" in evidence.finding


def test_low_host_similarity_does_not_claim_safety():
    records = [
        {
            "identity_percentage": 12.0,
            "alignment_length": 180,
            "query_coverage_percentage": 80.0,
            "subject_coverage_percentage": 75.0,
            "e_value": 0.01,
        }
    ]

    evidence = interpret_host_similarity(records)

    assert evidence.category == "host_similarity"
    assert "relatively low sequence similarity" in evidence.interpretation
    assert (
        "does not independently establish safety"
        in evidence.interpretation
    )


def test_high_host_similarity_requires_further_review():
    records = [
        {
            "identity_percentage": 67.0,
            "alignment_length": 240,
            "query_coverage_percentage": 90.0,
            "subject_coverage_percentage": 85.0,
            "e_value": 1e-20,
        }
    ]

    evidence = interpret_host_similarity(records)

    assert evidence.confidence == "high"
    assert "relatively strong sequence-similarity match" in (
        evidence.interpretation
    )
    assert "further investigation" in evidence.interpretation


def test_multiple_host_similarity_records_are_summarized():
    records = [
        {
            "identity_percentage": 12.0,
            "alignment_length": 180,
            "query_coverage_percentage": 80.0,
            "subject_coverage_percentage": 75.0,
            "e_value": 0.01,
        },
        {
            "identity_percentage": 45.0,
            "alignment_length": 220,
            "query_coverage_percentage": 85.0,
            "subject_coverage_percentage": 80.0,
            "e_value": 1e-10,
        },
    ]

    evidence = interpret_host_similarity(records)

    assert evidence.category == "host_similarity"
    assert "45.0%" in evidence.finding
    assert "1e-10" in evidence.finding

def test_high_identity_with_low_coverage_is_partial_similarity():
    records = [
        {
            "identity_percentage": 95.0,
            "alignment_length": 20,
            "query_coverage_percentage": 5.0,
            "subject_coverage_percentage": 4.0,
            "e_value": 1e-50,
        }
    ]

    evidence = interpret_host_similarity(records)

    assert evidence.category == "host_similarity"
    assert "high sequence identity" in evidence.interpretation
    assert "partial" in evidence.interpretation.lower()
    assert "safety" not in evidence.interpretation.lower()


def test_high_identity_with_broad_coverage_is_strong_similarity():
    records = [
        {
            "identity_percentage": 95.0,
            "alignment_length": 1500,
            "query_coverage_percentage": 92.0,
            "subject_coverage_percentage": 88.0,
            "e_value": 1e-50,
        }
    ]

    evidence = interpret_host_similarity(records)

    assert evidence.category == "host_similarity"
    assert "strong" in evidence.interpretation.lower()
    assert "broad" in evidence.interpretation.lower()
    assert "safety" in evidence.interpretation.lower()


def test_finding_includes_coverage():
    records = [
        {
            "identity_percentage": 95.0,
            "alignment_length": 1500,
            "query_coverage_percentage": 92.0,
            "subject_coverage_percentage": 88.0,
            "e_value": 1e-50,
        }
    ]

    evidence = interpret_host_similarity(records)

    assert "query coverage=92.0%" in evidence.finding
    assert "subject coverage=88.0%" in evidence.finding