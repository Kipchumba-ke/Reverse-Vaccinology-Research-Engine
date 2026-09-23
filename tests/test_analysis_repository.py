from app.models.analysis import Analysis
from app.repositories.analysis_repository import AnalysisRepository


def test_repository_can_save_analysis():
    repository = AnalysisRepository()

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

def test_repository_can_find_analysis_by_id():
    repository = AnalysisRepository()

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

def test_repository_returns_none_for_unknown_analysis():
    repository = AnalysisRepository()

    found = repository.find_by_id("does-not-exist")

    assert found is None