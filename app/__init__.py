from flask import Flask, request

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


def create_repository():
    engine = create_database_engine_from_environment()
    session_factory = create_session_factory(engine)
    session = session_factory()
    return AnalysisRepository(session)

def create_app(repository=None):
    app = Flask(__name__)
    if repository is None:
        repository = create_repository()

    app.config["ANALYSIS_REPOSITORY"] = repository

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

    return app