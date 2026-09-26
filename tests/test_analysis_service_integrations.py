from app.services.analysis_service import analyze_sequence


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