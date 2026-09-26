import pytest
import requests

from app.integrations.uniprot import fetch_protein_annotation
from app.analysis.interpretation import create_uniprot_annotation_evidence


def test_fetch_protein_annotation_returns_annotation():
    annotation = fetch_protein_annotation("P12345")

    assert annotation["accession"] == "P12345"


def test_fetch_protein_annotation_returns_protein_name(monkeypatch):
    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "primaryAccession": "P12345",
                "proteinDescription": {
                    "recommendedName": {
                        "fullName": {
                            "value": "Example protein"
                        }
                    }
                }
            }

    def fake_get(*args, **kwargs):
        return FakeResponse()

    monkeypatch.setattr(
        "app.integrations.uniprot.requests.get",
        fake_get,
    )

    annotation = fetch_protein_annotation("P12345")

    assert annotation["accession"] == "P12345"
    assert annotation["protein_name"] == "Example protein"


def test_fetch_protein_annotation_rejects_empty_accession():
    with pytest.raises(ValueError, match="Accession is required"):
        fetch_protein_annotation("")


def test_fetch_protein_annotation_raises_runtime_error_on_http_failure(monkeypatch):
    class FakeResponse:
        def raise_for_status(self):
            raise requests.HTTPError("404 Not Found")

    def fake_get(*args, **kwargs):
        return FakeResponse()

    monkeypatch.setattr(
        "app.integrations.uniprot.requests.get",
        fake_get,
    )

    with pytest.raises(RuntimeError, match="UniProt request failed"):
        fetch_protein_annotation("P12345")


def test_fetch_protein_annotation_raises_runtime_error_on_request_failure(monkeypatch):
    def fake_get(*args, **kwargs):
        raise requests.RequestException("Connection failed")

    monkeypatch.setattr(
        "app.integrations.uniprot.requests.get",
        fake_get,
    )

    with pytest.raises(RuntimeError, match="UniProt request failed"):
        fetch_protein_annotation("P12345")



def test_uniprot_annotation_can_be_converted_to_evidence():
    annotation = {
        "accession": "P12345",
        "protein_name": "Example protein",
    }

    evidence = create_uniprot_annotation_evidence(annotation)

    assert evidence.category == "uniprot_annotation"
    assert evidence.finding == "Example protein"
    assert "P12345" in evidence.interpretation


def test_uniprot_annotation_evidence_is_descriptive():
    annotation = {
        "accession": "P12345",
        "protein_name": "Example protein",
    }

    evidence = create_uniprot_annotation_evidence(annotation)

    assert "annotation" in evidence.interpretation.lower()
    assert "vaccine" not in evidence.interpretation.lower()
    assert "safety" not in evidence.interpretation.lower()


def test_fetch_protein_annotation_handles_missing_recommended_name(monkeypatch):
    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "primaryAccession": "P12345",
                "proteinDescription": {},
            }

    def fake_get(*args, **kwargs):
        return FakeResponse()

    monkeypatch.setattr(
        "app.integrations.uniprot.requests.get",
        fake_get,
    )

    annotation = fetch_protein_annotation("P12345")

    assert annotation["accession"] == "P12345"
    assert annotation["protein_name"] is None