from app.models.analysis import Analysis
from app.services.analysis_execution import execute_analysis
from app.repositories.analysis_repository import AnalysisRepository
from app.services.analysis_job import AnalysisJob


def test_execution_service_runs_analysis():
    analysis = Analysis(
        protein_id="P0A911",
        protein_name="Outer membrane protein A",
        organism="Escherichia coli O157:H7",
        accession="P0A911",
        sequence="MKT",
    )

    result = execute_analysis(analysis)

    assert result["protein"]["id"] == "P0A911"



def test_execution_marks_analysis_as_completed():
    analysis = Analysis(
        protein_id="P0A911",
        protein_name="Outer membrane protein A",
        organism="Escherichia coli O157:H7",
        accession="P0A911",
        sequence="MKT",
    )

    execute_analysis(analysis)

    assert analysis.status == "completed"


def test_execution_marks_analysis_as_failed_when_analysis_raises(monkeypatch):
    analysis = Analysis(
        protein_id="P0A911",
        protein_name="Outer membrane protein A",
        organism="Escherichia coli O157:H7",
        accession="P0A911",
        sequence="MKT",
    )

    def fail_analysis(*args, **kwargs):
        raise RuntimeError("Analysis failed")

    monkeypatch.setattr(
        "app.services.analysis_execution.analyze_sequence",
        fail_analysis,
    )

    try:
        execute_analysis(analysis)
    except RuntimeError:
        pass

    assert analysis.status == "failed"



def test_execution_persists_running_status(db_session, monkeypatch):
    repository = AnalysisRepository(db_session)

    analysis = Analysis(
        protein_id="P0A911",
        protein_name="Outer membrane protein A",
        organism="Escherichia coli O157:H7",
        accession="P0A911",
        sequence="MKT",
    )

    repository.save(analysis)
    db_session.commit()

    def inspect_running_status(*args, **kwargs):
        persisted = repository.find_by_id(analysis.id)

        assert persisted.status == "running"

        return {
            "protein": {
                "id": "P0A911",
            }
        }

    monkeypatch.setattr(
        "app.services.analysis_execution.analyze_sequence",
        inspect_running_status,
    )

    execute_analysis(analysis, repository)


def test_update_analysis_status(db_session):
    repository = AnalysisRepository(db_session)

    analysis = Analysis(
        protein_id="P0A911",
        protein_name="Outer membrane protein A",
        organism="Escherichia coli O157:H7",
        accession="P0A911",
        sequence="MKT",
    )

    repository.save(analysis)
    db_session.commit()

    analysis.status = "running"

    repository.update(analysis)
    db_session.commit()

    persisted = repository.find_by_id(analysis.id)

    assert persisted.status == "running"


def test_execution_persists_completed_status(db_session, monkeypatch):
    repository = AnalysisRepository(db_session)

    analysis = Analysis(
        protein_id="P0A911",
        protein_name="Outer membrane protein A",
        organism="Escherichia coli O157:H7",
        accession="P0A911",
        sequence="MKT",
    )

    repository.save(analysis)
    db_session.commit()

    monkeypatch.setattr(
        "app.services.analysis_execution.analyze_sequence",
        lambda *args, **kwargs: {
            "protein": {
                "id": "P0A911",
            }
        },
    )

    execute_analysis(analysis, repository)

    persisted = repository.find_by_id(analysis.id)

    assert persisted.status == "completed"



def test_execution_persists_failed_status(db_session, monkeypatch):
    repository = AnalysisRepository(db_session)

    analysis = Analysis(
        protein_id="P0A911",
        protein_name="Outer membrane protein A",
        organism="Escherichia coli O157:H7",
        accession="P0A911",
        sequence="MKT",
    )

    repository.save(analysis)
    db_session.commit()

    def fail_analysis(*args, **kwargs):
        raise RuntimeError("Analysis failed")

    monkeypatch.setattr(
        "app.services.analysis_execution.analyze_sequence",
        fail_analysis,
    )

    try:
        execute_analysis(analysis, repository)
    except RuntimeError:
        pass

    persisted = repository.find_by_id(analysis.id)

    assert persisted.status == "failed"



def test_analysis_job_runs_analysis():
    analysis = Analysis(
        protein_id="P0A911",
        protein_name="Outer membrane protein A",
        organism="Escherichia coli O157:H7",
        accession="P0A911",
        sequence="MKT",
    )

    job = AnalysisJob(analysis)

    result = job.run()

    assert result["protein"]["id"] == "P0A911"
    assert analysis.status == "completed"



def test_analysis_job_runs_with_repository(db_session):
    repository = AnalysisRepository(db_session)

    analysis = Analysis(
        protein_id="P0A911",
        protein_name="Outer membrane protein A",
        organism="Escherichia coli O157:H7",
        accession="P0A911",
        sequence="MKT",
    )

    repository.save(analysis)
    db_session.commit()

    job = AnalysisJob(analysis, repository)

    result = job.run()

    assert result["protein"]["id"] == "P0A911"

    persisted = repository.find_by_id(analysis.id)

    assert persisted.status == "completed"



def test_analysis_job_persists_failed_status(db_session, monkeypatch):
    repository = AnalysisRepository(db_session)

    analysis = Analysis(
        protein_id="P0A911",
        protein_name="Outer membrane protein A",
        organism="Escherichia coli O157:H7",
        accession="P0A911",
        sequence="MKT",
    )

    repository.save(analysis)
    db_session.commit()

    def fail_analysis(*args, **kwargs):
        raise RuntimeError("Analysis failed")

    monkeypatch.setattr(
        "app.services.analysis_execution.analyze_sequence",
        fail_analysis,
    )

    job = AnalysisJob(analysis, repository)

    try:
        job.run()
    except RuntimeError:
        pass

    persisted = repository.find_by_id(analysis.id)

    assert persisted.status == "failed"
