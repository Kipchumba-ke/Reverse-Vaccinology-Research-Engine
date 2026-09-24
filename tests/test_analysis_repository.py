import pytest

from uuid import uuid4

from sqlalchemy.exc import IntegrityError, PendingRollbackError

from app.models.analysis import Analysis
from app.repositories.analysis_repository import AnalysisRepository
from app.models.analysis_orm import AnalysisModel


def test_repository_can_save_analysis(db_session):
    repository = AnalysisRepository(db_session)

    analysis = Analysis(
        protein_id="sp|P12345|EXAMPLE",
        protein_name="Example protein",
        organism="Escherichia coli",
        accession="P12345",
        sequence="MKTAYIAKQRQISFVKSHFSRQ",
        status="completed",
    )

    saved = repository.save(analysis)

    assert saved == analysis

def test_repository_can_find_analysis_by_id(db_session):
    repository = AnalysisRepository(db_session)

    analysis = Analysis(
        protein_id="sp|P12345|EXAMPLE",
        protein_name="Example protein",
        organism="Escherichia coli",
        accession="P12345",
        sequence="MKTAYIAKQRQISFVKSHFSRQ",
        status="completed",
    )

    saved = repository.save(analysis)

    found = repository.find_by_id(saved.id)

    assert found == saved

def test_repository_returns_none_for_unknown_analysis(db_session):
    repository = AnalysisRepository(db_session)

    found = repository.find_by_id(uuid4())

    assert found is None

def test_repository_saves_analysis_to_postgresql(db_session):
    repository = AnalysisRepository(db_session)
    analysis = Analysis(
        protein_id="sp|P12345|EXAMPLE",
        protein_name="Example protein",
        organism="Escherichia coli",
        accession="P12345",
        sequence="MKTAYIAKQRQISFVKSHFSRQ",
        status="completed",
    )

    saved = repository.save(analysis)

    db_row = db_session.get(AnalysisModel, analysis.id)

    assert saved == analysis
    assert db_row is not None
    assert db_row.protein_id == "sp|P12345|EXAMPLE"


def test_repository_does_not_commit_transaction(db_session):
    repository = AnalysisRepository(db_session)

    analysis = Analysis(
        protein_id="sp|P99999|TRANSACTION",
        protein_name="Transaction test protein",
        organism="Escherichia coli",
        accession="P99999",
        sequence="MKTAYIAKQRQISFVKSHFSRQ",
        status="completed",
    )

    repository.save(analysis)

    assert db_session.in_transaction()


def test_repository_round_trip_preserves_analysis(db_session):
    repository = AnalysisRepository(db_session)

    analysis = Analysis(
        protein_id="sp|P54321|ROUNDTRIP",
        protein_name="Round trip protein",
        organism="Staphylococcus aureus",
        accession="P54321",
        sequence="MKTAYIAKQRQISFVKSHFSRQ",
        status="completed",
    )

    repository.save(analysis)

    found = repository.find_by_id(analysis.id)

    assert found == analysis


def test_repository_finds_analysis_by_uuid(db_session):
    repository = AnalysisRepository(db_session)

    analysis = Analysis(
        protein_id="sp|P11111|UUID",
        protein_name="UUID test protein",
        organism="Escherichia coli",
        accession="P11111",
        sequence="MKTAYIAKQRQISFVKSHFSRQ",
        status="completed",
    )

    repository.save(analysis)

    found = repository.find_by_id(analysis.id)

    assert found is not None
    assert found.id == analysis.id


def test_repository_rejects_duplicate_analysis_id(db_session):
    repository = AnalysisRepository(db_session)

    analysis = Analysis(
        protein_id="sp|P22222|DUPLICATE",
        protein_name="Duplicate test protein",
        organism="Escherichia coli",
        accession="P22222",
        sequence="MKTAYIAKQRQISFVKSHFSRQ",
        status="completed",
    )

    repository.save(analysis)

    duplicate = Analysis(
        id=analysis.id,
        protein_id="sp|P33333|DUPLICATE",
        protein_name="Another protein",
        organism="Escherichia coli",
        accession="P33333",
        sequence="GATAYIAKQRQISFVKSHFSRQ",
        status="pending",
    )

    with pytest.raises(IntegrityError):
        repository.save(duplicate)

def test_repository_requires_rollback_after_duplicate_id_failure(db_session):
    repository = AnalysisRepository(db_session)

    analysis = Analysis(
        protein_id="sp|P22222|DUPLICATE",
        protein_name="Duplicate test protein",
        organism="Escherichia coli",
        accession="P22222",
        sequence="MKTAYIAKQRQISFVKSHFSRQ",
        status="completed",
    )

    repository.save(analysis)

    duplicate = Analysis(
        id=analysis.id,
        protein_id="sp|P33333|DUPLICATE",
        protein_name="Another protein",
        organism="Escherichia coli",
        accession="P33333",
        sequence="GATAYIAKQRQISFVKSHFSRQ",
        status="pending",
    )

    with pytest.raises(IntegrityError):
        repository.save(duplicate)

    with pytest.raises(PendingRollbackError):
        repository.find_by_id(analysis.id)

