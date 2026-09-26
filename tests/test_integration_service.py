import pytest

from app.services.integration_service import run_integrations


def test_run_integrations_combines_external_evidence(monkeypatch):
    monkeypatch.setattr(
        "app.services.integration_service.fetch_protein_annotation",
        lambda accession: {
            "accession": accession,
            "protein_name": "Example protein",
        },
    )

    monkeypatch.setattr(
        "app.services.integration_service.run_blast_analysis",
        lambda sequence, database, source, confidence, description: [
            {"category": "host_similarity"}
        ],
    )

    monkeypatch.setattr(
        "app.services.integration_service.run_msa",
        lambda sequences: ["ACDE-", "ACD-E"],
    )

    result = run_integrations(
        sequence="ACDE",
        accession="P12345",
        blast_database="host_db",
        msa_sequences=["ACDE", "ACDE"],
    )

    assert result["uniprot"]["protein_name"] == "Example protein"
    assert result["blast"] == [{"category": "host_similarity"}]
    assert result["msa"] == ["ACDE-", "ACD-E"]

def test_run_integrations_requires_accession():

    with pytest.raises(ValueError, match="Accession is required"):
        run_integrations(
            sequence="ACDE",
            accession="",
            blast_database="host_db",
            msa_sequences=["ACDE", "ACDE"],
        )

def test_run_integrations_requires_blast_database(monkeypatch):
    monkeypatch.setattr(
        "app.services.integration_service.fetch_protein_annotation",
        lambda accession: {
            "accession": accession,
            "protein_name": "Example protein",
        },
    )

    with pytest.raises(ValueError, match="BLAST database is required"):
        run_integrations(
            sequence="ACDE",
            accession="P12345",
            blast_database="",
            msa_sequences=["ACDE", "ACDE"],
        )


def test_run_integrations_requires_msa_sequences(monkeypatch):
    monkeypatch.setattr(
        "app.services.integration_service.fetch_protein_annotation",
        lambda accession: {
            "accession": accession,
            "protein_name": "Example protein",
        },
    )

    monkeypatch.setattr(
        "app.services.integration_service.run_blast_analysis",
        lambda sequence, database, source, confidence, description: [],
    )

    with pytest.raises(ValueError, match="At least two sequences are required"):
        run_integrations(
            sequence="ACDE",
            accession="P12345",
            blast_database="host_db",
            msa_sequences=[],
        )

def test_run_integrations_propagates_uniprot_failure(monkeypatch):
    def fail_uniprot(accession):
        raise RuntimeError("UniProt request failed")

    monkeypatch.setattr(
        "app.services.integration_service.fetch_protein_annotation",
        fail_uniprot,
    )

    with pytest.raises(RuntimeError, match="UniProt request failed"):
        run_integrations(
            sequence="ACDE",
            accession="P12345",
            blast_database="host_db",
            msa_sequences=["ACDE", "ACDE"],
        )

def test_run_integrations_propagates_blast_failure(monkeypatch):
    monkeypatch.setattr(
        "app.services.integration_service.fetch_protein_annotation",
        lambda accession: {
            "accession": accession,
            "protein_name": "Example protein",
        },
    )

    def fail_blast(sequence, database, source, confidence, description):
        raise RuntimeError("MSA execution failed")

    monkeypatch.setattr(
        "app.services.integration_service.run_blast_analysis",
        fail_blast,
    )

    with pytest.raises(RuntimeError, match="MSA execution failed"):
        run_integrations(
            sequence="ACDE",
            accession="P12345",
            blast_database="host_db",
            msa_sequences=["ACDE", "ACDE"],
        )


def test_run_integrations_propagates_msa_failure(monkeypatch):
    monkeypatch.setattr(
        "app.services.integration_service.fetch_protein_annotation",
        lambda accession: {
            "accession": accession,
            "protein_name": "Example protein",
        },
    )

    monkeypatch.setattr(
        "app.services.integration_service.run_blast_analysis",
        lambda sequence, database, source, confidence, description: [],
    )

    def fail_msa(sequences):
        raise RuntimeError("MSA execution failed")

    monkeypatch.setattr(
        "app.services.integration_service.run_msa",
        fail_msa,
    )

    with pytest.raises(RuntimeError, match="MSA execution failed"):
        run_integrations(
            sequence="ACDE",
            accession="P12345",
            blast_database="host_db",
            msa_sequences=["ACDE", "ACDE"],
        )