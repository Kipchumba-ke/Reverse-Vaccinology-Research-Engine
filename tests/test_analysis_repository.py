from uuid import uuid4

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
