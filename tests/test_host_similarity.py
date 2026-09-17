import pytest

from app.analysis.host_similarity import (
    create_host_similarity_evidence,
)


def test_create_host_similarity_evidence():
    result = create_host_similarity_evidence(
        target_id="pathogen_gene_A",
        host_id="host_protein_123",
        similarity_method="BLASTP",
        identity_percentage=18.5,
        alignment_length=142,
        query_coverage_percentage=80.0,
        subject_coverage_percentage=75.0,
        e_value=0.42,
        source="Host protein database",
        confidence="medium",
        description=(
            "Low sequence similarity was observed "
            "against the supplied host protein."
        ),
    )

    assert result.target_id == "pathogen_gene_A"
    assert result.host_id == "host_protein_123"
    assert result.similarity_method == "BLASTP"
    assert result.identity_percentage == 18.5


def test_host_similarity_to_dict():
    result = create_host_similarity_evidence(
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

    data = result.to_dict()

    assert data["target_id"] == "target_A"
    assert data["host_id"] == "host_A"
    assert data["e_value"] == 1.5


def test_empty_target_id_rejected():
    with pytest.raises(ValueError):
        create_host_similarity_evidence(
            target_id="",
            host_id="host_A",
            similarity_method="BLASTP",
            identity_percentage=20,
            alignment_length=100,
            query_coverage_percentage=80.0,
            subject_coverage_percentage=75.0,
            e_value=1,
            source="Database",
            confidence="medium",
            description="Evidence.",
        )


def test_invalid_identity_rejected():
    with pytest.raises(ValueError):
        create_host_similarity_evidence(
            target_id="target_A",
            host_id="host_A",
            similarity_method="BLASTP",
            identity_percentage=120,
            alignment_length=100,
            query_coverage_percentage=80.0,
            subject_coverage_percentage=75.0,
            e_value=1,
            source="Database",
            confidence="medium",
            description="Evidence.",
        )


def test_invalid_alignment_length_rejected():
    with pytest.raises(ValueError):
        create_host_similarity_evidence(
            target_id="target_A",
            host_id="host_A",
            similarity_method="BLASTP",
            identity_percentage=20,
            alignment_length=0,
            query_coverage_percentage=80.0,
            subject_coverage_percentage=75.0,
            e_value=1,
            source="Database",
            confidence="medium",
            description="Evidence.",
        )


def test_negative_e_value_rejected():
    with pytest.raises(ValueError):
        create_host_similarity_evidence(
            target_id="target_A",
            host_id="host_A",
            similarity_method="BLASTP",
            identity_percentage=20,
            alignment_length=100,
            query_coverage_percentage=80.0,
            subject_coverage_percentage=75.0,
            e_value=-1,
            source="Database",
            confidence="medium",
            description="Evidence.",
        )


def test_invalid_confidence_rejected():
    with pytest.raises(ValueError):
        create_host_similarity_evidence(
            target_id="target_A",
            host_id="host_A",
            similarity_method="BLASTP",
            identity_percentage=20,
            alignment_length=100,
            query_coverage_percentage=80.0,
            subject_coverage_percentage=75.0,
            e_value=1,
            source="Database",
            confidence="certain",
            description="Evidence.",
        )

def test_query_coverage_must_be_between_zero_and_one_hundred():
    with pytest.raises(ValueError, match="Query coverage percentage"):
        create_host_similarity_evidence(
            target_id="target_1",
            host_id="host_1",
            similarity_method="BLASTP",
            identity_percentage=30.0,
            alignment_length=200,
            query_coverage_percentage=101.0,
            subject_coverage_percentage=80.0,
            e_value=1e-5,
            source="Example database",
            confidence="medium",
            description="Test evidence.",
        )


def test_subject_coverage_must_be_between_zero_and_one_hundred():
    with pytest.raises(
        ValueError,
        match="Subject coverage percentage",
    ):
        create_host_similarity_evidence(
            target_id="target_1",
            host_id="host_1",
            similarity_method="BLASTP",
            identity_percentage=30.0,
            alignment_length=200,
            query_coverage_percentage=80.0,
            subject_coverage_percentage=-1.0,
            e_value=1e-5,
            source="Example database",
            confidence="medium",
            description="Test evidence.",
        )

