
import csv

import pytest

from app.integrations.essentiality import fetch_essentiality_evidence


FIELDS = [
    "gene_id",
    "organism",
    "essentiality_status",
    "source",
    "confidence",
    "description",
    "accession",
]



def write_dataset(tmp_path, rows, fields=FIELDS):
    path = tmp_path / "essentiality.tsv"

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fields,
            delimiter="\t",
            extrasaction="ignore",
        )
        writer.writeheader()

        for row in rows:
            writer.writerow({
                field: row.get(field, "")
                for field in fields
            })

    return str(path)


def make_row(**overrides):
    row = {
        "gene_id": "geneA",
        "organism": "Example bacterium",
        "essentiality_status": "essential",
        "source": "Published experimental dataset",
        "confidence": "high",
        "description": "Essentiality reported in the source dataset.",
        "accession": "ABC123.1",
    }
    row.update(overrides)
    return row


def test_fetches_matching_essentiality_evidence_by_protein_id(tmp_path):
    path = write_dataset(tmp_path, [make_row()])

    result = fetch_essentiality_evidence(
        dataset_path=path,
        protein_id="geneA",
        accession=None,
        organism="Example bacterium",
    )

    assert result["status"] == "available"
    assert len(result["evidence"]) == 1

    evidence = result["evidence"][0]
    assert evidence.gene_id == "geneA"
    assert evidence.organism == "Example bacterium"
    assert evidence.essentiality_status == "essential"
    assert evidence.source == "Published experimental dataset"


def test_fetches_essentiality_evidence_by_accession(tmp_path):
    path = write_dataset(tmp_path, [make_row()])

    result = fetch_essentiality_evidence(
        dataset_path=path,
        protein_id="different-id",
        accession="ABC123.1",
        organism="Example bacterium",
    )

    assert result["status"] == "available"
    assert len(result["evidence"]) == 1
    assert result["evidence"][0].gene_id == "geneA"


def test_does_not_match_evidence_from_another_organism(tmp_path):
    path = write_dataset(tmp_path, [make_row()])

    result = fetch_essentiality_evidence(
        dataset_path=path,
        protein_id="geneA",
        accession="ABC123.1",
        organism="Different bacterium",
    )

    assert result["status"] == "no_matching_evidence"
    assert result["evidence"] == []


def test_reports_unconfigured_dataset():
    result = fetch_essentiality_evidence(
        dataset_path=None,
        protein_id="geneA",
        accession="ABC123.1",
        organism="Example bacterium",
    )

    assert result["status"] == "not_configured"
    assert result["evidence"] == []


def test_reports_missing_dataset_file(tmp_path):
    path = tmp_path / "missing.tsv"

    result = fetch_essentiality_evidence(
        dataset_path=str(path),
        protein_id="geneA",
        accession=None,
        organism="Example bacterium",
    )

    assert result["status"] == "lookup_failed"
    assert result["evidence"] == []


def test_requires_organism_for_matching(tmp_path):
    path = write_dataset(tmp_path, [make_row()])

    result = fetch_essentiality_evidence(
        dataset_path=path,
        protein_id="geneA",
        accession=None,
        organism=None,
    )

    assert result["status"] == "organism_required"
    assert result["evidence"] == []


def test_requires_protein_identifier_for_matching(tmp_path):
    path = write_dataset(tmp_path, [make_row()])

    result = fetch_essentiality_evidence(
        dataset_path=path,
        protein_id=None,
        accession=None,
        organism="Example bacterium",
    )

    assert result["status"] == "identifier_required"
    assert result["evidence"] == []


def test_ignores_malformed_essentiality_record(tmp_path):
    path = write_dataset(
        tmp_path,
        [make_row(essentiality_status="probably-essential")],
    )

    result = fetch_essentiality_evidence(
        dataset_path=path,
        protein_id="geneA",
        accession=None,
        organism="Example bacterium",
    )

    assert result["status"] == "no_matching_evidence"
    assert result["evidence"] == []


def test_reports_missing_required_dataset_columns(tmp_path):
    path = write_dataset(
        tmp_path,
        [make_row()],
        fields=["gene_id", "organism"],
    )

    result = fetch_essentiality_evidence(
        dataset_path=path,
        protein_id="geneA",
        accession=None,
        organism="Example bacterium",
    )

    assert result["status"] == "lookup_failed"
    assert result["evidence"] == []
