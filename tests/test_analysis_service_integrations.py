from unittest.mock import patch
from app.services.analysis_service import analyze_sequence
from app.analysis.essentiality import create_essentiality_evidence
from app.services.analysis_service import analyze_fasta_records
from app.analysis.pipeline import analyze_protein as real_analyze_protein


def test_analyze_sequence_runs_external_integrations(monkeypatch):
    calls = {}

    def fake_integrations(
        sequence,
        accession,
        blast_database,
        msa_sequences,
    ):
        calls["sequence"] = sequence
        calls["accession"] = accession
        calls["blast_database"] = blast_database
        calls["msa_sequences"] = msa_sequences

        return {
            "uniprot": {
                "accession": accession,
                "protein_name": "Example protein",
            },
            "blast": [],
            "msa": ["ACDE-", "ACD-E"],
        }

    monkeypatch.setattr(
        "app.services.analysis_service.run_integrations",
        fake_integrations,
    )

    result = analyze_sequence(
        "ACDE",
        protein_id="P12345",
        protein_name="Example protein",
        organism="Example organism",
        accession="P12345",
        blast_database="host_db",
        msa_sequences=["ACDE", "ACDE"],
    )

    assert calls["sequence"] == "ACDE"
    assert calls["accession"] == "P12345"
    assert calls["blast_database"] == "host_db"
    assert calls["msa_sequences"] == ["ACDE", "ACDE"]


def test_analyze_sequence_includes_integration_results(monkeypatch):
    monkeypatch.setattr(
        "app.services.analysis_service.run_integrations",
        lambda sequence, accession, blast_database, msa_sequences: {
            "uniprot": {
                "accession": accession,
                "protein_name": "Example protein",
            },
            "blast": [
                {
                    "category": "host_similarity",
                    "finding": "BLAST host match",
                    "interpretation": "Sequence similarity requires further review.",
                    "confidence": "medium",
                }
            ],
            "msa": ["ACDE-", "ACD-E"],
        },
    )

    report = analyze_sequence(
        "ACDE",
        accession="P12345",
        blast_database="host_db",
        msa_sequences=["ACDE", "ACDE"],
    )

    assert report["integrations"]["uniprot"]["accession"] == "P12345"
    assert report["integrations"]["blast"][0]["category"] == "host_similarity"
    assert report["integrations"]["msa"] == ["ACDE-", "ACD-E"]
    assert report["conservation"]["summary"] is not None


def test_analyze_sequence_builds_conservation_from_msa(monkeypatch):
    monkeypatch.setattr(
        "app.services.analysis_service.run_integrations",
        lambda sequence, accession, blast_database, msa_sequences: {
            "uniprot": {
                "accession": accession,
                "protein_name": "Example protein",
            },
            "blast": [],
            "msa": ["ACDE-", "ACD--"],
        },
    )

    report = analyze_sequence(
        "ACDE",
        accession="P12345",
        blast_database="host_db",
        msa_sequences=["ACDE", "ACDE"],
    )

    assert report["conservation"]["summary"] is not None
    assert report["conservation"]["summary"]["sequence_count"] == 2
    assert report["conservation"]["summary"]["conservation_percentage"] == 100.0

def test_analyze_sequence_includes_conservation_summary():
    report = analyze_sequence(
        "ACDE",
        msa_sequences=[
            "ACDE",
            "ACD-",
        ],
    )

    assert report["conservation"]["summary"] is not None
    assert report["conservation"]["summary"]["sequence_count"] == 2

@patch("app.services.analysis_service.run_blast_analysis")
@patch("app.services.analysis_service.fetch_essentiality_evidence")
def test_analysis_service_attaches_essentiality_and_host_evidence(
    mock_essentiality,
    mock_blast,
):
    essentiality_evidence = create_essentiality_evidence(
        gene_id="geneA",
        organism="Example bacterium",
        essentiality_status="essential",
        source="Published experimental dataset",
        confidence="high",
        description="Essentiality reported in the source dataset.",
    )

    mock_essentiality.return_value = {
        "evidence": [essentiality_evidence],
        "status": "available",
        "message": "One matching record found.",
    }

    mock_blast.return_value = []

    with patch.dict(
        "os.environ",
        {
            "HOST_BLAST_DATABASE": "/mock/host_database",
            "ESSENTIALITY_DATA_PATH": "/mock/essentiality.tsv",
        },
    ):
        report = analyze_sequence(
            "MKTAYIAKQRQISFVKSHFSRQ",
            protein_id="geneA",
            organism="Example bacterium",
        )

    assert report["evidence_status"]["essentiality"]["status"] == "available"
    assert "essentiality" in report["evidence_status"]
    assert "host_similarity" in report["evidence_status"]
    evidence = report["evidence"]["essentiality"]
    assert len(evidence) == 1
    assert evidence[0]["gene_id"] == "geneA"
    assert evidence[0]["essentiality_status"] == "essential"
    assert evidence[0]["source"] == "Published experimental dataset"
    essentiality_interpretation = next(
        item
        for item in report["interpretations"]
        if item["category"] == "essentiality"
    )
    assert "essential" in essentiality_interpretation["finding"]
    assert (
        "Essentiality reported in the source dataset."
        in essentiality_interpretation["interpretation"]
    )


@patch("app.services.analysis_service.fetch_essentiality_evidence")
def test_analysis_service_reports_unavailable_essentiality(
    mock_essentiality,
):
    mock_essentiality.return_value = {
        "evidence": [],
        "status": "no_matching_evidence",
        "message": "No matching record found.",
    }

    report = analyze_sequence("MKTAYIAKQRQISFVKSHFSRQ")

    assert report["evidence_status"]["essentiality"]["status"] == (
        "no_matching_evidence"
    )
    assert report["evidence"]["essentiality"] == []

    interpretation = next(
        item
        for item in report["interpretations"]
        if item["category"] == "essentiality"
    )
    assert "unavailable" in interpretation["interpretation"].lower()
    assert "non-essential" not in interpretation["interpretation"].lower()


@patch("app.services.analysis_service.fetch_essentiality_evidence")
def test_analysis_service_survives_essentiality_lookup_failure(
    mock_essentiality,
):
    mock_essentiality.side_effect = RuntimeError(
        "Essentiality dataset unavailable."
    )

    report = analyze_sequence("MKTAYIAKQRQISFVKSHFSRQ")

    assert report["evidence_status"]["essentiality"]["status"] == (
        "lookup_failed"
    )
    assert report["evidence"]["essentiality"] == []
    assert any(
        item["category"] == "essentiality"
        for item in report["interpretations"]
    )

@patch("app.analysis.workflow.analyze_protein")
def test_multi_record_analysis_runs_pipeline_once_per_protein(
    mock_analyze_protein,
):
    records = [
        {
            "id": "protein_a",
            "sequence": "ACDE",
            "description": "Protein A",
            "organism": "Example organism",
        },
        {
            "id": "protein_b",
            "sequence": "FGHI",
            "description": "Protein B",
            "organism": "Example organism",
        },
    ]

    mock_analyze_protein.side_effect = (
        lambda sequence, **kwargs: real_analyze_protein(
            sequence, **kwargs
        )
    )
