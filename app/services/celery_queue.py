import os

from celery import Celery

from app.services.job_queue import Queue
from app.database import (
    create_database_engine_from_environment,
    create_session_factory,
)
from app.repositories.analysis_repository import AnalysisRepository
from app.services.analysis_execution import execute_analysis


celery_app = Celery(
    "reverse_vaccinology",
    broker=os.environ.get(
        "CELERY_BROKER_URL",
        "redis://localhost:6379/0",
    ),
    backend=os.environ.get(
        "CELERY_RESULT_BACKEND",
        "redis://localhost:6379/0",
    ),
)


def _seconds(name: str, default: int) -> int:
    raw = os.environ.get(name, "").strip()

    if not raw:
        return default

    try:
        value = int(raw)
    except ValueError as error:
        raise RuntimeError(f"{name} must be a whole number of seconds.") from error

    if value <= 0:
        raise RuntimeError(f"{name} must be greater than zero.")

    return value


# An analysis that runs past the soft limit is stopped and marked failed
# (execute_analysis records the failure). The hard limit then kills the task
# if it is stuck somewhere that cannot be interrupted, such as a BioLib call.
# Keep both above the slowest predictor (PSORTB_TIMEOUT_SECONDS).
_SOFT_LIMIT = _seconds("ANALYSIS_SOFT_TIME_LIMIT_SECONDS", 3300)
_HARD_LIMIT = max(_seconds("ANALYSIS_TIME_LIMIT_SECONDS", 3600), _SOFT_LIMIT + 60)

celery_app.conf.update(
    task_soft_time_limit=_SOFT_LIMIT,
    task_time_limit=_HARD_LIMIT,
)


class CeleryQueue:
    def enqueue(self, job):
        execute_analysis_task.delay(job.analysis_id)
        return job.analysis_id

    def run(self, job_id):
        raise NotImplementedError


@celery_app.task
def execute_analysis_task(analysis_id):
    engine = create_database_engine_from_environment()
    session_factory = create_session_factory(engine)
    session = session_factory()

    try:
        repository = AnalysisRepository(session)
        analysis = repository.find_by_id(analysis_id)

        if analysis is None:
            raise ValueError(f"Analysis {analysis_id} not found.")

        result = execute_analysis(
            analysis,
            repository,
        )

        session.commit()

        return result

    except Exception:
        session.rollback()
        raise

    finally:
        session.close()
        engine.dispose()
