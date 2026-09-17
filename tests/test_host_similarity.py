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
            e_value=1,
            source="Database",
            confidence="certain",
            description="Evidence.",
        )