import os
import pytest
from uuid import uuid4


from app.models.analysis import Analysis
from app.services.analysis_execution import execute_analysis
from app.repositories.analysis_repository import AnalysisRepository
from app.services.analysis_job import AnalysisJob
from app.services.job_queue import JobQueue, Queue
from app.services.analysis_worker import AnalysisWorker
from app.services.analysis_submission import AnalysisSubmissionService
from app.services.celery_queue import CeleryQueue
from app.database import create_engine, create_session_factory
from app.services.celery_queue import execute_analysis_task
from app.models.analysis_orm import AnalysisModel


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



def test_analysis_job_exposes_analysis_id():
    analysis = Analysis(
        protein_id="P0A911",
        protein_name="Outer membrane protein A",
        organism="Escherichia coli O157:H7",
        accession="P0A911",
        sequence="MKT",
    )

    job = AnalysisJob(analysis)

    assert job.analysis_id == analysis.id



def test_job_queue_can_enqueue_analysis_job():
    queue = JobQueue()

    analysis = Analysis(
        protein_id="P0A911",
        protein_name="Outer membrane protein A",
        organism="Escherichia coli O157:H7",
        accession="P0A911",
        sequence="MKT",
    )

    job = AnalysisJob(analysis)

    job_id = queue.enqueue(job)

    assert job_id == analysis.id



def test_job_queue_stores_enqueued_job():
    queue = JobQueue()

    analysis = Analysis(
        protein_id="P0A911",
        protein_name="Outer membrane protein A",
        organism="Escherichia coli O157:H7",
        accession="P0A911",
        sequence="MKT",
    )

    job = AnalysisJob(analysis)

    queue.enqueue(job)

    assert queue.get(analysis.id) is job



def test_job_queue_runs_enqueued_job():
    queue = JobQueue()

    analysis = Analysis(
        protein_id="P0A911",
        protein_name="Outer membrane protein A",
        organism="Escherichia coli O157:H7",
        accession="P0A911",
        sequence="MKT",
    )

    job = AnalysisJob(analysis)

    queue.enqueue(job)

    result = queue.run(analysis.id)

    assert result["protein"]["id"] == "P0A911"
    assert analysis.status == "completed"



def test_job_queue_raises_for_unknown_job():
    queue = JobQueue()

    with pytest.raises(ValueError, match="Job .* not found"):
        queue.run(uuid4())



def test_analysis_worker_runs_queued_job():
    queue = JobQueue()

    analysis = Analysis(
        protein_id="P0A911",
        protein_name="Outer membrane protein A",
        organism="Escherichia coli O157:H7",
        accession="P0A911",
        sequence="MKT",
    )

    job = AnalysisJob(analysis)
    job_id = queue.enqueue(job)

    worker = AnalysisWorker(queue)

    result = worker.run(job_id)

    assert result["protein"]["id"] == "P0A911"
    assert analysis.status == "completed"



def test_analysis_worker_propagates_unknown_job():
    queue = JobQueue()
    worker = AnalysisWorker(queue)

    with pytest.raises(ValueError, match="Job .* not found"):
        worker.run("missing-job")



def test_analysis_worker_accepts_queue_like_object():
    class FakeQueue:
        def __init__(self):
            self.called_with = None

        def run(self, job_id):
            self.called_with = job_id
            return {"status": "completed"}

    queue = FakeQueue()
    worker = AnalysisWorker(queue)

    result = worker.run("analysis-123")

    assert result == {"status": "completed"}
    assert queue.called_with == "analysis-123"



def test_job_queue_implements_queue_contract():
    queue = JobQueue()

    assert isinstance(queue, Queue)



def test_job_queue_enqueue_does_not_run_job():
    queue = JobQueue()

    analysis = Analysis(
        protein_id="P0A911",
        protein_name="Outer membrane protein A",
        organism="Escherichia coli O157:H7",
        accession="P0A911",
        sequence="MKT",
    )

    job = AnalysisJob(analysis)

    job_id = queue.enqueue(job)

    assert job_id == analysis.id
    assert analysis.status == "pending"

class FakeRepository:
    def __init__(self):
        self.saved_analysis = None

    def save(self, analysis):
        self.saved_analysis = analysis
        return analysis

def test_submit_analysis_creates_and_enqueues_job():
    repository = FakeRepository()
    queue = JobQueue()

    service = AnalysisSubmissionService(repository, queue)

    analysis_id = service.submit(
        sequence="MKT",
        protein_id="P0A911",
        protein_name="Outer membrane protein A",
        organism="Escherichia coli O157:H7",
        accession="P0A911",
    )

    assert analysis_id is not None

    analysis = repository.saved_analysis

    assert analysis.id == analysis_id
    assert analysis.sequence == "MKT"
    assert analysis.status == "pending"
    assert queue.get(analysis_id) is not None



def test_submit_analysis_does_not_execute_job():
    repository = FakeRepository()
    queue = JobQueue()

    service = AnalysisSubmissionService(repository, queue)

    analysis_id = service.submit(
        sequence="MKT",
        protein_id="P0A911",
    )

    analysis = repository.saved_analysis

    assert analysis_id == analysis.id
    assert analysis.status == "pending"



def test_submit_analysis_does_not_enqueue_when_persistence_fails():
    class FailingRepository:
        def save(self, analysis):
            raise RuntimeError("Database unavailable")

    repository = FailingRepository()
    queue = JobQueue()

    service = AnalysisSubmissionService(repository, queue)

    with pytest.raises(RuntimeError, match="Database unavailable"):
        service.submit(
            sequence="MKT",
            protein_id="P0A911",
        )

    assert queue._jobs == {}



def test_submit_analysis_propagates_queue_failure():
    class FailingQueue:
        def enqueue(self, job):
            raise RuntimeError("Queue unavailable")

    repository = FakeRepository()
    queue = FailingQueue()

    service = AnalysisSubmissionService(repository, queue)

    with pytest.raises(RuntimeError, match="Queue unavailable"):
        service.submit(
            sequence="MKT",
            protein_id="P0A911",
        )

    assert repository.saved_analysis is not None
    assert repository.saved_analysis.status == "pending"



def test_submit_analysis_returns_enqueued_analysis_id():
    repository = FakeRepository()
    queue = JobQueue()

    service = AnalysisSubmissionService(repository, queue)

    analysis_id = service.submit(
        sequence="MKT",
        protein_id="P0A911",
    )

    queued_job = queue.get(analysis_id)

    assert queued_job is not None
    assert queued_job.analysis_id == analysis_id

def test_celery_queue_implements_queue_contract():

    queue = CeleryQueue()

    assert isinstance(queue, Queue)



def test_celery_task_loads_analysis_from_repository(monkeypatch):

    test_database_url = os.environ["TEST_DATABASE_URL"]
    engine = create_engine(test_database_url)
    session_factory = create_session_factory(engine)
    setup_session = session_factory()

    try:
        analysis = Analysis(
            sequence="MKTIIALSYIFCLVFADYKDDDDA",
            protein_id="P12345",
            protein_name="Test Protein",
            organism="Test organism",
            accession="ACC123",
        )

        repository = AnalysisRepository(setup_session)
        repository.save(analysis)
        setup_session.commit()

        executed = {}

        def fake_execute_analysis(loaded_analysis, repository):
            executed["analysis"] = loaded_analysis
            executed["repository"] = repository

        monkeypatch.setattr(
            "app.services.celery_queue.execute_analysis",
            fake_execute_analysis,
        )

        monkeypatch.setenv(
            "DATABASE_URL",
            test_database_url,
        )

        execute_analysis_task(analysis.id)

        assert executed["analysis"].id == analysis.id
        assert executed["analysis"].sequence == analysis.sequence
        deleted_analysis = setup_session.get(
            AnalysisModel,
            analysis.id,
        )

        assert deleted_analysis is not None

        setup_session.delete(deleted_analysis)
        setup_session.commit()

        assert setup_session.get(
            AnalysisModel,
            analysis.id,
        ) is None

    finally:
        setup_session.close()
        engine.dispose()

def test_execute_analysis_task_is_registered_with_celery():

    assert hasattr(execute_analysis_task, "delay")
    assert hasattr(execute_analysis_task, "apply_async")

def test_celery_queue_enqueues_analysis_job(monkeypatch):
    analysis = Analysis(
        protein_id="P0A911",
        protein_name="Outer membrane protein A",
        organism="Escherichia coli",
        accession="P0A911",
        sequence="MKT",
    )

    job = AnalysisJob(analysis)

    called = {}

    def fake_delay(analysis_id):
        called["analysis_id"] = analysis_id

    monkeypatch.setattr(
        "app.services.celery_queue.execute_analysis_task.delay",
        fake_delay,
    )

    queue = CeleryQueue()

    analysis_id = queue.enqueue(job)

    assert analysis_id == analysis.id
    assert called["analysis_id"] == analysis.id

def test_submit_analysis_with_celery_queue_dispatches_task(monkeypatch, db_session):
    repository = AnalysisRepository(db_session)
    queue = CeleryQueue()

    called = {}

    def fake_delay(analysis_id):
        called["analysis_id"] = analysis_id

    monkeypatch.setattr(
        execute_analysis_task,
        "delay",
        fake_delay,
    )

    service = AnalysisSubmissionService(repository, queue)

    analysis_id = service.submit(
        sequence="MKT",
        protein_id="P0A911",
    )

    assert called["analysis_id"] == analysis_id
