from flask import Flask, request
from uuid import UUID
import jwt

from app.database import (
    create_database_engine_from_environment,
    create_session_factory,
)
from app.repositories.analysis_repository import AnalysisRepository
from app.services.analysis_service import (
    analyze_sequence,
    analyze_fasta_records,
    run_analysis
)
from app.input.fasta import parse_fasta_records
from werkzeug.exceptions import RequestEntityTooLarge
from app.services.analysis_submission import AnalysisSubmissionService
from app.services.job_queue import JobQueue
from app.services.authentication import get_authenticated_user_id


def create_repository():
    engine = create_database_engine_from_environment()
    session_factory = create_session_factory(engine)
    session = session_factory()
    return AnalysisRepository(session)

def create_app(repository=None, queue=None):
    app = Flask(__name__)

    owns_repository = repository is None

    if owns_repository:
        repository = create_repository()

    if queue is None:
        queue = JobQueue()

    app.config["ANALYSIS_REPOSITORY"] = repository
    app.config["ANALYSIS_QUEUE"] = queue

    @app.teardown_appcontext
    def close_repository(error):
        if owns_repository:
            repository.session.close()

    @app.errorhandler(RequestEntityTooLarge)
    def handle_request_entity_too_large(error):
        return {"error": "Request payload is too large."}, 413

    @app.post("/api/analyze")
    @app.post("/api/v1/analyze")
    def analyze():
        if "file" in request.files:
            uploaded_file = request.files["file"]

            if not uploaded_file.filename:
                return {"error": "FASTA file is required."}, 400

            filename = uploaded_file.filename.lower()
            if not filename.endswith((".fasta", ".fa", ".fna")):
                return {
                    "error": "Unsupported file type. FASTA files are required."
                }, 400

            try:
                fasta_text = uploaded_file.read().decode("utf-8")
                records = parse_fasta_records(fasta_text)

                result = analyze_fasta_records(records)

                return result, 200

            except (UnicodeDecodeError, ValueError) as error:
                return {"error": str(error)}, 400
        data = request.get_json(silent=True)

        if not data:
            return {"error": "JSON request body is required."}, 400
        if "sequence" not in data:
            return {"error": "Sequence is required."}, 400

        try:
            report = run_analysis(
                data["sequence"],
                repository=repository,
                protein_id=data.get("protein_id"),
                protein_name=data.get("protein_name"),
                organism=data.get("organism"),
                accession=data.get("accession"),
            )

            repository.session.commit()

        except (TypeError, ValueError) as error:
            repository.session.rollback()
            return {"error": str(error)}, 400

        return report, 200

    @app.post("/api/analyses")
    def submit_analysis():
        repository = app.config["ANALYSIS_REPOSITORY"]
        
        try:
            user_id = get_authenticated_user_id(request)
        except jwt.InvalidTokenError:
            return {"error": "Invalid authentication token."}, 401

        data = request.get_json(silent=True)

        if not data:
            return {"error": "JSON request body is required."}, 400

        if "sequence" not in data:
            return {"error": "Sequence is required."}, 400

        try:
            service = AnalysisSubmissionService(
                repository,
                app.config["ANALYSIS_QUEUE"],
            )

            analysis_id = service.submit(
                user_id=user_id,
                sequence=data["sequence"],
                protein_id=data.get("protein_id"),
                protein_name=data.get("protein_name"),
                organism=data.get("organism"),
                accession=data.get("accession"),
            )

            repository.session.commit()

        except (TypeError, ValueError) as error:
            repository.session.rollback()
            return {"error": str(error)}, 400

        except RuntimeError as error:
            repository.session.rollback()
            return {"error": str(error)}, 500

        return {
            "analysis_id": str(analysis_id),
            "status": "pending",
        }, 202

    @app.get("/api/analyses/<analysis_id>")
    def get_analysis_status(analysis_id):
        repository = app.config["ANALYSIS_REPOSITORY"]

        try:
            user_id = get_authenticated_user_id(request)
        except ValueError as error:
            return {"error": str(error)}, 401

        try:
            analysis_id = UUID(analysis_id)
        except ValueError:
            return {"error": "Invalid analysis ID."}, 400

        analysis = repository.find_by_id(analysis_id)

        if analysis is None:
            return {"error": "Analysis not found."}, 404

        if analysis.user_id != user_id:
            return {"error": "You do not have access to this analysis."}, 403

        return {
            "analysis_id": str(analysis.id),
            "status": analysis.status,
        }, 200
    @app.get("/api/protected")
    def protected():

        try:
            user_id = get_authenticated_user_id(request)
        except ValueError as error:
            return {"error": str(error)}, 401

        return {
            "message": "Authenticated.",
            "user_id": str(user_id),
        }, 200

    return app