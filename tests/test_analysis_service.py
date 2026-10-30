import pytest
import json

from app.models.analysis import Analysis
from app.repositories.analysis_repository import AnalysisRepository
from app.services.analysis_service import (
    analyze_sequence,
    analyze_fasta_records,
    create_analysis,
    persist_analysis,
    run_analysis
)
from app.models.analysis_orm import AnalysisModel


def test_analyze_sequence_returns_protein_report():
    sequence = "MKTAYIAKQRQISFVKSHFSRQ"

    report = analyze_sequence(sequence)

    assert "protein" in report
    assert "measurements" in report
    assert "evidence" in report
    assert "interpretations" in report
    assert "candidate_assessment" in report
    assert "limitations" in report
    assert "conservation" in report
    assert "metadata" in report

def test_analyze_sequence_preserves_protein_metadata():
    report = analyze_sequence(
        "MKTAYIAKQRQISFVKSHFSRQ",
        protein_id="sp|P12345|EXAMPLE",
        protein_name="Example protein",
        organism="Escherichia coli",
        accession="P12345",
    )

    assert report["protein"]["id"] == "sp|P12345|EXAMPLE"
    assert report["protein"]["name"] == "Example protein"
    assert report["protein"]["organism"] == "Escherichia coli"
    assert report["protein"]["accession"] == "P12345"

def test_analyze_fasta_records_with_single_record_returns_report():
    records = [
        {
            "id": "sp|P12345|EXAMPLE",
            "description": "Example protein",
            "organism": "Escherichia coli",
            "accession": "P12345",
            "sequence": "MKTAYIAKQRQISFVKSHFSRQ",
        }
    ]

    report = analyze_fasta_records(records)

    assert report["protein"]["id"] == "sp|P12345|EXAMPLE"
    assert report["protein"]["name"] == "Example protein"
    assert report["protein"]["organism"] == "Escherichia coli"
    assert report["protein"]["accession"] == "P12345"

def test_analyze_fasta_records_with_multiple_records_returns_workflow_dict():
    records = [
        {
            "id": "sp|P12345|EXAMPLE1",
            "description": "Example protein 1",
            "organism": "Escherichia coli",
            "accession": "P12345",
            "sequence": "MKTAYIAKQRQISFVKSHFSRQ",
        },
        {
            "id": "sp|P67890|EXAMPLE2",
            "description": "Example protein 2",
            "organism": "Escherichia coli",
            "accession": "P67890",
            "sequence": "MKTAYIAKQRQISFVKSHFSRQ",
        },
    ]

    result = analyze_fasta_records(records)
    json.dumps(result)

    assert result["records"] == records
    assert len(result["protein_analyses"]) == 2
    assert result["alignment"] is not None
    assert result["conservation"] is not None
    for protein_report in result["protein_analyses"]:
        assert "protein" in protein_report
        assert "measurements" in protein_report
        assert "evidence" in protein_report
        assert "interpretations" in protein_report
        assert "candidate_assessment" in protein_report
        assert "limitations" in protein_report
        assert "conservation" in protein_report
        assert "metadata" in protein_report
        assert protein_report["conservation"]["status"] == "completed"
        assert protein_report["conservation"]["summary"] is not None

        assessment = protein_report["candidate_assessment"]

        assert any(
            "conserved positions" in item.lower()
            for item in assessment["supporting_evidence"]
        )

        assert not any(
            "multiple-sequence alignment and conservation analysis"
            in item.lower()
            for item in assessment["missing_evidence"]
        )
    assert result["protein_analyses"][0]["protein"]["id"] == "sp|P12345|EXAMPLE1"
    assert result["protein_analyses"][1]["protein"]["id"] == "sp|P67890|EXAMPLE2"


def test_persist_analysis_saves_analysis(db_session):
    repository = AnalysisRepository(db_session)

    analysis = Analysis(
        protein_id="sp|P12345|TEST_PROTEIN",
        protein_name="Test protein",
        organism="Escherichia coli",
        accession="P12345",
        sequence="MKTAYIAKQRQISFVKSHFSRQ",
        status="completed",
    )

    saved = persist_analysis(analysis, repository)

    assert saved == analysis

    persisted = repository.find_by_id(analysis.id)

    assert persisted == analysis


def test_create_analysis_builds_analysis_from_input():
    analysis = create_analysis(
        "MKTAYIAKQRQISFVKSHFSRQ",
        protein_id="sp|P12345|EXAMPLE",
        protein_name="Example protein",
        organism="Escherichia coli",
        accession="P12345",
    )

    assert isinstance(analysis, Analysis)
    assert analysis.protein_id == "sp|P12345|EXAMPLE"
    assert analysis.protein_name == "Example protein"
    assert analysis.organism == "Escherichia coli"
    assert analysis.accession == "P12345"
    assert analysis.sequence == "MKTAYIAKQRQISFVKSHFSRQ"
    assert analysis.status == "pending"


def test_create_analysis_normalizes_sequence():
    analysis = create_analysis(
        " mktay iakqrqisfvkshfsrq ",
    )

    assert analysis.sequence == "MKTAYIAKQRQISFVKSHFSRQ"


def test_create_analysis_rejects_invalid_sequence():
    with pytest.raises(ValueError):
        create_analysis("MKTAY123INVALID")


def test_create_and_persist_analysis_round_trip(db_session):
    repository = AnalysisRepository(db_session)

    analysis = create_analysis(
        " mktay iakqrqisfvkshfsrq ",
        protein_id="sp|P12345|EXAMPLE",
        protein_name="Example protein",
        organism="Escherichia coli",
        accession="P12345",
    )

    persisted = persist_analysis(analysis, repository)

    saved = repository.find_by_id(persisted.id)

    assert saved == analysis


def test_run_analysis_persists_analysis_and_returns_report(db_session):
    repository = AnalysisRepository(db_session)

    report = run_analysis(
        " mktay iakqrqisfvkshfsrq ",
        repository=repository,
        protein_id="sp|P12345|EXAMPLE",
        protein_name="Example protein",
        organism="Escherichia coli",
        accession="P12345",
    )

    assert report["protein"]["id"] == "sp|P12345|EXAMPLE"
    assert report["protein"]["name"] == "Example protein"
    assert report["protein"]["organism"] == "Escherichia coli"
    assert report["protein"]["accession"] == "P12345"
    assert report["protein"]["sequence"] == "MKTAYIAKQRQISFVKSHFSRQ"

    analyses = db_session.query(AnalysisModel).all()

    assert len(analyses) == 1
    assert analyses[0].protein_id == "sp|P12345|EXAMPLE"
    assert analyses[0].sequence == "MKTAYIAKQRQISFVKSHFSRQ"


def test_run_analysis_does_not_persist_invalid_sequence(db_session):
    repository = AnalysisRepository(db_session)

    with pytest.raises(ValueError):
        run_analysis(
            "INVALID123",
            repository=repository,
            protein_id="sp|P12345|INVALID",
            protein_name="Invalid protein",
        )

    analyses = db_session.query(AnalysisModel).all()

    assert analyses == []


def test_run_analysis_rolls_back_when_analysis_fails(db_session, monkeypatch):
    repository = AnalysisRepository(db_session)

    def failing_analyze_sequence(*args, **kwargs):
        raise RuntimeError("analysis failed")

    monkeypatch.setattr(
        "app.services.analysis_service.analyze_sequence",
        failing_analyze_sequence,
    )

    with pytest.raises(RuntimeError, match="analysis failed"):
        run_analysis(
            "MKTAYIAKQRQISFVKSHFSRQ",
            repository=repository,
            protein_id="sp|P12345|FAILURE",
            protein_name="Failure test protein",
        )

    db_session.rollback()

    analyses = db_session.query(AnalysisModel).all()

    assert analyses == []


def test_db_session_commit_does_not_leak_between_tests(db_session):
    analysis = AnalysisModel(
        protein_id="TEST-ISOLATION",
        sequence="MKTAYIAKQRQISFVKSHFSRQ",
        status="pending",
    )

    db_session.add(analysis)
    db_session.commit()

    assert db_session.query(AnalysisModel).count() == 1

def test_db_session_rolls_back_all_changes_after_test(db_session):
    analysis = AnalysisModel(
        protein_id="TEST-ROLLBACK",
        sequence="MKTAYIAKQRQISFVKSHFSRQ",
        status="pending",
    )

    db_session.add(analysis)
    db_session.commit()

    assert db_session.query(AnalysisModel).count() == 1

def test_analyze_sequence_includes_uniprot_localization_evidence(monkeypatch):
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

    monkeypatch.setattr(
        "app.services.analysis_service.fetch_protein_annotation",
        lambda accession: annotation,
    )

    report = analyze_sequence(
        "MKTAYIAKQRQISFVKSHFSRQ",
        accession="P12345",
    )

    localization = report["evidence"]["localization"]

    assert len(localization) == 1
    assert localization[0]["location"] == "Cell membrane"
    assert localization[0]["source"] == "UniProt"
    assert "ECO:0000269" in localization[0]["description"]


def test_analyze_fasta_records_attaches_localization_to_correct_protein(
    monkeypatch,
):
    records = [
        {
            "id": "protein_1",
            "description": "Protein one",
            "accession": "P12345",
            "sequence": "MKTAYIAKQRQISFVKSHFSRQ",
        },
        {
            "id": "protein_2",
            "description": "Protein two",
            "accession": "P67890",
            "sequence": "MKTAYIAKQRQISFVKSHFSRQ",
        },
    ]

    annotations = {
        "P12345": {
            "accession": "P12345",
            "protein_name": "Protein one",
            "localization_annotations": [
                {
                    "location": "Cell membrane",
                    "source": "UniProt",
                    "evidence_codes": ["ECO:0000269"],
                }
            ],
        },
        "P67890": {
            "accession": "P67890",
            "protein_name": "Protein two",
            "localization_annotations": [
                {
                    "location": "Cytoplasm",
                    "source": "UniProt",
                    "evidence_codes": ["ECO:0000256"],
                }
            ],
        },
    }

    monkeypatch.setattr(
        "app.services.analysis_service.fetch_protein_annotation",
        lambda accession: annotations[accession],
    )

    result = analyze_fasta_records(records)

    protein_reports = result["protein_analyses"]
    first = protein_reports[0]["evidence"]["localization"]
    second = protein_reports[1]["evidence"]["localization"]

    assert len(first) == 1
    assert first[0]["location"] == "Cell membrane"
    assert "ECO:0000269" in first[0]["description"]

    assert len(second) == 1
    assert second[0]["location"] == "Cytoplasm"
    assert "ECO:0000256" in second[0]["description"]

def test_analyze_fasta_records_preserves_epath_status_per_protein(
    monkeypatch,
):
    records = [
        {
            "id": "protein_1",
            "description": "Protein one",
            "accession": "P12345",
            "sequence": "MKTAYIAKQRQISFVKSHFSRQ",
        },
        {
            "id": "protein_2",
            "description": "Protein two",
            "accession": "P67890",
            "sequence": "MKTAYIAKQRQISFVKSHFSRQ",
        },
    ]

    statuses = {
        "protein_1": {
            "status": "available",
            "message": "Experimental essentiality evidence is available.",
        },
        "protein_2": {
            "status": "unclassified",
            "message": "The matching record does not establish essentiality.",
        },
    }

    def mock_fetch_external_evidence(
        sequence,
        protein_id=None,
        accession=None,
        organism=None,
        epath_gene_id=None,
        epath_ko_id=None,
        host_reference=None,
    ):
        # Return the expected ePath status for this specific protein.
        status = statuses[protein_id]

        return {
            "essentiality": {
                "status": "not_requested",
                "message": "Essentiality lookup was not requested.",
            },
            "essentiality_evidence": [],
            "epath_essentiality": status,
            "epath_essentiality_evidence": [],
            "host_similarity": {
                "status": "not_requested",
                "message": "Host similarity lookup was not requested.",
            },
            "host_similarity_evidence": [],
        }


    monkeypatch.setattr(
        "app.services.analysis_service._fetch_external_evidence",
        mock_fetch_external_evidence,
    )

    monkeypatch.setattr(
        "app.services.analysis_service.fetch_protein_annotation",
        lambda accession: {
            "accession": accession,
            "protein_name": accession,
            "localization_annotations": [],
        },
    )

    result = analyze_fasta_records(records)

    protein_reports = {
        report["protein"]["id"]: report
        for report in result["protein_analyses"]
    }

    first_status = protein_reports["protein_1"]["evidence_status"][
        "epath_essentiality"
    ]
    second_status = protein_reports["protein_2"]["evidence_status"][
        "epath_essentiality"
    ]

    assert first_status["status"] == "available"
    assert (
        first_status["message"]
        == "Experimental essentiality evidence is available."
    )

    assert second_status["status"] == "unclassified"
    assert (
        second_status["message"]
        == "The matching record does not establish essentiality."
    )

def test_analyze_sequence_enriches_missing_protein_name(monkeypatch):
    annotation = {
        "accession": "P12345",
        "protein_name": "Example protein",
        "localization_annotations": [],
    }

    monkeypatch.setattr(
        "app.services.analysis_service.fetch_protein_annotation",
        lambda accession: annotation,
    )

    report = analyze_sequence(
        "MKTAYIAKQRQISFVKSHFSRQ",
        accession="P12345",
    )

    assert report["protein"]["name"] == "Example protein"


def test_analyze_sequence_preserves_supplied_protein_name(monkeypatch):
    annotation = {
        "accession": "P12345",
        "protein_name": "UniProt protein name",
        "localization_annotations": [],
    }

    monkeypatch.setattr(
        "app.services.analysis_service.fetch_protein_annotation",
        lambda accession: annotation,
    )

    report = analyze_sequence(
        "MKTAYIAKQRQISFVKSHFSRQ",
        protein_name="User supplied name",
        accession="P12345",
    )

    assert report["protein"]["name"] == "User supplied name"


def test_analyze_fasta_records_passes_user_organism_to_each_lookup(
    monkeypatch,
):
    records = [
        {
            "id": "protein_1",
            "description": "Protein one",
            "accession": "P12345",
            "sequence": "MKTAYIAKQRQISFVKSHFSRQ",
        },
        {
            "id": "protein_2",
            "description": "Protein two",
            "accession": "P67890",
            "sequence": "MKTAYIAKQRQISFVKSHFSRQ",
        },
    ]

    received_organisms = {}

    def mock_fetch_external_evidence(
        sequence,
        protein_id=None,
        accession=None,
        organism=None,
        epath_gene_id=None,
        epath_ko_id=None,
        host_reference=None,
    ):
        received_organisms[protein_id] = organism

        return {
            "essentiality": {
                "status": "not_requested",
                "message": "Essentiality lookup not requested.",
            },
            "essentiality_evidence": [],
            "epath_essentiality": {
                "status": "organism_required" if not organism else "not_found",
                "message": "Test result.",
            },
            "epath_essentiality_evidence": [],
            "host_similarity": {
                "status": "not_requested",
                "message": "Host similarity lookup not requested.",
            },
            "host_similarity_evidence": [],
        }

    monkeypatch.setattr(
        "app.services.analysis_service._fetch_external_evidence",
        mock_fetch_external_evidence,
    )

    monkeypatch.setattr(
        "app.services.analysis_service.fetch_localization_result",
        lambda accession: {
            "evidence": [],
            "status": "not_found",
            "source": "test",
            "message": "No localization in test.",
        },
    )

    analyze_fasta_records(
        records,
        organism="Escherichia coli",
    )

    assert received_organisms == {
        "protein_1": "Escherichia coli",
        "protein_2": "Escherichia coli",
    }
