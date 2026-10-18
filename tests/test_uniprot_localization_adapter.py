
from app.services.integration_service import (
    convert_uniprot_localizations,
)


def test_convert_uniprot_localizations_preserves_source_and_evidence_codes():
    annotation = {
        "accession": "P12345",
        "protein_name": "Example protein",
        "localization_annotations": [
            {
                "location": "Cell membrane",
                "source": "UniProt",
                "evidence_codes": ["ECO:0000269"],
            }
        ],
    }

    evidence = convert_uniprot_localizations(annotation)

    assert len(evidence) == 1
    assert evidence[0].location == "Cell membrane"
    assert evidence[0].source == "UniProt"
    assert evidence[0].confidence == "low"
    assert "ECO:0000269" in evidence[0].description


def test_convert_uniprot_localizations_handles_no_annotations():
    annotation = {
        "accession": "P12345",
        "localization_annotations": [],
    }

    assert convert_uniprot_localizations(annotation) == []
