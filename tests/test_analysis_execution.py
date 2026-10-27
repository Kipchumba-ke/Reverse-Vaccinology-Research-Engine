import os
import pytest
from uuid import uuid4


from app import create_app
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

def test_execution_persists_analysis_report(db_session, monkeypatch):
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

    report = {
        "protein": {
            "id": "P0A911",
        },
        "sequence": "MKT",
        "length": 3,
    }

    monkeypatch.setattr(
        "app.services.analysis_execution.analyze_sequence",
        lambda *args, **kwargs: report,
    )

    execute_analysis(analysis, repository)

    persisted = repository.find_by_id(analysis.id)

    assert persisted.report == report

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



def test_submit_analysis_does_not_dispatch_when_persistence_fails():
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


def test_create_app_uses_celery_queue_by_default():
    app = create_app()
    assert isinstance(
        app.config["ANALYSIS_QUEUE"],
        CeleryQueue,
    )


def test_execution_routes_fasta_to_fasta_workflow(monkeypatch):
    analysis = Analysis(
        sequence=">protein_1 Example protein\nMKT\n"
    )
    captured = {}

    def fake_fasta_workflow(records, **kwargs):
        captured["records"] = records
        captured["kwargs"] = kwargs
        return {"workflow": "fasta"}

    def unexpected_sequence_analysis(*args, **kwargs):
        raise AssertionError(
            "FASTA input must not be passed to analyze_sequence"
        )

    monkeypatch.setattr(
        "app.services.analysis_execution.analyze_fasta_records",
        fake_fasta_workflow,
        raising=False,
    )
    monkeypatch.setattr(
        "app.services.analysis_execution.analyze_sequence",
        unexpected_sequence_analysis,
    )

    result = execute_analysis(analysis)

    assert result == {"workflow": "fasta"}
    assert captured["records"][0]["sequence"] == "MKT"
    assert analysis.status == "completed"


def test_execution_processes_persisted_fasta_content(
    db_session, monkeypatch
):
    repository = AnalysisRepository(db_session)
    fasta_content = ">protein_1 Example protein\nMKT\n"

    analysis = Analysis(sequence=fasta_content)
    repository.save(analysis)
    db_session.commit()

    persisted = repository.find_by_id(analysis.id)

    assert persisted.sequence == fasta_content

    captured = {}

    def fake_fasta_workflow(records, **kwargs):
        captured["records"] = records
        captured["kwargs"] = kwargs
        return {"workflow": "fasta", "protein_count": len(records)}

    monkeypatch.setattr(
        "app.services.analysis_execution.analyze_fasta_records",
        fake_fasta_workflow,
    )

    result = execute_analysis(persisted, repository)
    db_session.commit()

    assert result == {"workflow": "fasta", "protein_count": 1}
    assert captured["records"][0]["sequence"] == "MKT"
    assert persisted.status == "completed"

    saved_result = repository.find_by_id(analysis.id)
    assert saved_result.status == "completed"
    assert saved_result.report == result

def test_execution_passes_persisted_epath_identifiers_to_analysis(
    db_session, monkeypatch
):
    repository = AnalysisRepository(db_session)

    analysis = Analysis(
        organism="Escherichia coli K-12 MG1655",
        sequence="MKT",
        epath_gene_id="b3945",
        epath_ko_id="K00005",
    )

    repository.save(analysis)
    db_session.commit()

    persisted = repository.find_by_id(analysis.id)

    assert persisted is not None
    assert persisted.epath_gene_id == "b3945"
    assert persisted.epath_ko_id == "K00005"

    captured = {}
    expected_report = {
        "protein_id": "test-protein",
        "essentiality_evidence": [],
    }

    def fake_analyze_sequence(sequence, **kwargs):
        captured["sequence"] = sequence
        captured["kwargs"] = kwargs
        return expected_report

    monkeypatch.setattr(
        "app.services.analysis_execution.analyze_sequence",
        fake_analyze_sequence,
    )

    result = execute_analysis(persisted, repository)
    db_session.commit()

    assert result == expected_report
    assert captured["sequence"] == "MKT"
    assert captured["kwargs"]["epath_gene_id"] == "b3945"
    assert captured["kwargs"]["epath_ko_id"] == "K00005"
    assert captured["kwargs"]["organism"] == "Escherichia coli K-12 MG1655"

    saved_result = repository.find_by_id(analysis.id)

    assert saved_result.status == "completed"
    assert saved_result.report == expected_report
    assert saved_result.epath_gene_id == "b3945"
    assert saved_result.epath_ko_id == "K00005"

def test_execution_passes_epath_identifiers_for_single_record_fasta(
    monkeypatch,
):
    analysis = Analysis(
        sequence=">protein_1 Example protein\nMKT\n",
        organism="Escherichia coli K-12 MG1655",
        epath_gene_id="b3945",
        epath_ko_id="K00005",
    )

    captured = {}

    def fake_fasta_workflow(
        records,
        epath_gene_id=None,
        epath_ko_id=None,
        organism=None,
        host_reference=None,
    ):
        captured["records"] = records
        captured["epath_gene_id"] = epath_gene_id
        captured["epath_ko_id"] = epath_ko_id
        captured["organism"] = organism
        captured["host_reference"] = host_reference
        return {"workflow": "fasta"}

    monkeypatch.setattr(
        "app.services.analysis_execution.analyze_fasta_records",
        fake_fasta_workflow,
    )

    result = execute_analysis(analysis)

    assert result == {"workflow": "fasta"}
    assert captured["epath_gene_id"] == "b3945"
    assert captured["epath_ko_id"] == "K00005"
    assert captured["organism"] == "Escherichia coli K-12 MG1655"
    assert analysis.status == "completed"
