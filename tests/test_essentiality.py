import pytest

from app.analysis.essentiality import (
    create_essentiality_evidence,
)


def test_create_essentiality_evidence():
    result = create_essentiality_evidence(
        gene_id="geneA",
        organism="Example bacterium",
        essentiality_status="essential",
        source="Experimental knockout study",
        confidence="high",
        description="Loss of the gene prevented viable growth.",
    )

    assert result.gene_id == "geneA"
    assert result.organism == "Example bacterium"
    assert result.essentiality_status == "essential"
    assert result.confidence == "high"


def test_essentiality_evidence_to_dict():
    result = create_essentiality_evidence(
        gene_id="geneA",
        organism="Example bacterium",
        essentiality_status="essential",
        source="Database",
        confidence="medium",
        description="Curated essentiality annotation.",
    )

    data = result.to_dict()

    assert data["gene_id"] == "geneA"
    assert data["essentiality_status"] == "essential"


def test_empty_gene_id_rejected():
    with pytest.raises(ValueError):
        create_essentiality_evidence(
            gene_id="",
            organism="Example bacterium",
            essentiality_status="essential",
            source="Database",
            confidence="high",
            description="Evidence.",
        )


def test_invalid_status_rejected():
    with pytest.raises(ValueError):
        create_essentiality_evidence(
            gene_id="geneA",
            organism="Example bacterium",
            essentiality_status="probably_essential",
            source="Database",
            confidence="high",
            description="Evidence.",
        )


def test_empty_source_rejected():
    with pytest.raises(ValueError):
        create_essentiality_evidence(
            gene_id="geneA",
            organism="Example bacterium",
            essentiality_status="essential",
            source="",
            confidence="high",
            description="Evidence.",
        )


def test_invalid_confidence_rejected():
    with pytest.raises(ValueError):
        create_essentiality_evidence(
            gene_id="geneA",
            organism="Example bacterium",
            essentiality_status="essential",
            source="Database",
            confidence="certain",
            description="Evidence.",
        )


def test_empty_description_rejected():
    with pytest.raises(ValueError):
        create_essentiality_evidence(
            gene_id="geneA",
            organism="Example bacterium",
            essentiality_status="essential",
            source="Database",
            confidence="high",
            description="",
        )