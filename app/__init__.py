import os

from flask import Flask, g, request, send_file, jsonify
from flask_cors import CORS
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
from werkzeug.middleware.proxy_fix import ProxyFix
from app.services.analysis_submission import AnalysisSubmissionService
from app.services.celery_queue import CeleryQueue
from app.services.authentication import get_authenticated_user_id
from app.services.analysis_job import AnalysisJob
from app.services.auth_service import AuthService
from app.repositories.user_repository import UserRepository
from app.models.user_orm import UserModel
from app.reporting.pdf_export import generate_report_pdf
from app.services.rate_limit import (
    build_default_rules,
    build_rate_limiter_from_environment,
    install_rate_limiting,
)
from app.utils.limits import get_max_request_bytes


DEFAULT_CORS_ORIGIN = "http://localhost:5173"


def _get_allowed_origins() -> list[str]:
    """Return allowed CORS origins from CORS_ALLOWED_ORIGINS.

    The variable holds a comma-separated list of origins. It defaults
    to the local Vite development server.
    """
    configured = os.environ.get("CORS_ALLOWED_ORIGINS", DEFAULT_CORS_ORIGIN)

    origins = [
        origin.strip()
        for origin in configured.split(",")
        if origin.strip()
    ]

    return origins or [DEFAULT_CORS_ORIGIN]


_session_factory_cache = None


def _get_session_factory():
    """Return a shared session factory, building the engine only once.

    The cache is keyed on the factory-building functions so that
    replacing them (for example in tests) rebuilds the factory.
    """
    global _session_factory_cache

    key = (
        create_database_engine_from_environment,
        create_session_factory,
    )

    if _session_factory_cache is None or _session_factory_cache[0] != key:
        engine = create_database_engine_from_environment()
        _session_factory_cache = (key, create_session_factory(engine))

    return _session_factory_cache[1]


def create_repository():
    """Create a repository bound to a brand-new session."""
    session = _get_session_factory()()
    return AnalysisRepository(session)


class _RequestScopedRepository:
    """Resolves to a repository whose session belongs to one request.

    Sharing a single SQLAlchemy session across concurrent requests is
    unsafe, so each request lazily gets its own repository, which is
    closed when the request's application context ends.
    """

    def __init__(self, resolve):
        self._resolve = resolve

    def __getattr__(self, name):
        return getattr(self._resolve(), name)

def _get_trusted_proxy_count() -> int:
    raw_value = os.environ.get("TRUSTED_PROXY_COUNT", "0").strip() or "0"

    try:
        return max(0, int(raw_value))
    except ValueError as error:
        raise RuntimeError(
            "TRUSTED_PROXY_COUNT must be a whole number."
        ) from error


def create_app(repository=None, queue=None, rate_limiter=None):
    app = Flask(__name__)

    app.config["MAX_CONTENT_LENGTH"] = get_max_request_bytes()

    proxy_count = _get_trusted_proxy_count()

    if proxy_count:
        # Trust X-Forwarded-For from exactly this many reverse proxies so
        # rate limiting sees the real client address.
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=proxy_count)

    CORS(app, origins=_get_allowed_origins())

    owns_repository = repository is None

    if owns_repository:
        def resolve_request_repository():
            if "analysis_repository" not in g:
                g.analysis_repository = create_repository()
            return g.analysis_repository

        repository = _RequestScopedRepository(resolve_request_repository)

    if queue is None:
        queue = CeleryQueue()

    app.config["ANALYSIS_REPOSITORY"] = repository
    app.config["ANALYSIS_QUEUE"] = queue

    @app.teardown_appcontext
    def close_repository(error):
        if not owns_repository:
            return

        request_repository = g.pop("analysis_repository", None)

        if request_repository is not None:
            request_repository.session.close()

    if rate_limiter is None:
        rate_limiter = build_rate_limiter_from_environment()

    if rate_limiter is not None:
        install_rate_limiting(
            app,
            rate_limiter,
            build_default_rules(),
            get_user_id=get_authenticated_user_id,
        )

    @app.errorhandler(RequestEntityTooLarge)
    def handle_request_entity_too_large(error):
        return {"error": "Request payload is too large."}, 413

    @app.post("/api/analyze")
    @app.post("/api/v1/analyze")
    def analyze():
        try:
            get_authenticated_user_id(request)
        except ValueError as error:
            return {"error": str(error)}, 401

        
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

                result = analyze_fasta_records(
                    records,
                    organism=request.form.get("organism"),
                    epath_gene_id=request.form.get("epath_gene_id"),
                    epath_ko_id=request.form.get("epath_ko_id"),
                    host_reference=request.form.get("host_reference"),
                )

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
                msa_sequences=data.get("msa_sequences"),
                epath_gene_id=data.get("epath_gene_id"),
                epath_ko_id=data.get("epath_ko_id"),
                host_reference=data.get("host_reference"),
            )

            repository.session.commit()

        except (TypeError, ValueError) as error:
            repository.session.rollback()
            return {"error": str(error)}, 400

        response = {
            key: value
            for key, value in report.items()
            if key != "evidence_status"
        }
        return jsonify(response), 200

    @app.post("/api/login")
    def login():
        repository = app.config["ANALYSIS_REPOSITORY"]
        user_repository = UserRepository(repository.session)

        data = request.get_json(silent=True)

        if not data:
            return {"error": "JSON request body is required."}, 400

        if "email" not in data or "password" not in data:
            return {"error": "Email and password are required."}, 400

        try:
            service = AuthService(user_repository)

            result = service.login(
                data["email"],
                data["password"],
            )

        except ValueError as error:
            return {"error": str(error)}, 401

        return {
            "user_id": str(result["user_id"]),
            "token": result["token"],
        }, 200

    @app.post("/api/register")
    def register():
        repository = app.config["ANALYSIS_REPOSITORY"]
        user_repository = UserRepository(repository.session)

        data = request.get_json(silent=True)

        if not data:
            return {"error": "JSON request body is required."}, 400

        if "email" not in data or "password" not in data:
            return {"error": "Email and password are required."}, 400

        try:
            service = AuthService(user_repository)

            user = service.register(
                data["email"],
                data["password"],
            )

            repository.session.commit()

        except ValueError as error:
            repository.session.rollback()
            return {"error": str(error)}, 400

        return {
            "user_id": str(user.id),
        }, 201

    @app.get("/api/analyses")
    def list_analyses():
        try:
            user_id = get_authenticated_user_id(request)
        except ValueError as error:
            return jsonify({"error": str(error)}), 401

        if not user_id:
            return jsonify({"error": "Authentication required"}), 401

        analyses = repository.find_all_by_user_id(user_id)

        history = []

        for analysis in analyses:
            report = analysis.report or {}
            protein = report.get("protein") or {}

            history.append({
                "analysis_id": str(analysis.id),
                "protein_id": analysis.protein_id or protein.get("id"),
                "protein_name": (
                    analysis.protein_name or protein.get("name")
                ),
                "organism": analysis.organism or protein.get("organism"),
                "accession": analysis.accession or protein.get("accession"),
                "status": analysis.status,
                "created_at": (
                    analysis.created_at.isoformat()
                    if analysis.created_at
                    else None
                )
            })

        return jsonify({"analyses": history}), 200

    @app.post("/api/analyses")
    def submit_analysis():
        repository = app.config["ANALYSIS_REPOSITORY"]
        
        try:
            user_id = get_authenticated_user_id(request)
        except ValueError as error:
            return {"error": str(error)}, 401

        data = request.get_json(silent=True)

        if not data:
            return {"error": "JSON request body is required."}, 400

        has_sequence = "sequence" in data
        has_fasta_content = "fasta_content" in data

        if not has_sequence and not has_fasta_content:
            return {"error": "Sequence is required."}, 400

        if has_sequence and has_fasta_content:
            return {
                "error": "Provide either a protein sequence or FASTA content, not both."
            }, 400

        if has_fasta_content:
            try:
                parse_fasta_records(data["fasta_content"])
            except (TypeError, ValueError) as error:
                return {"error": str(error)}, 400

            input_sequence = data["fasta_content"]
        else:
            input_sequence = data["sequence"]

        try:
            service = AnalysisSubmissionService(
                repository,
                app.config["ANALYSIS_QUEUE"],
            )

            analysis_id = service.submit(
                user_id=user_id,
                sequence=input_sequence,
                protein_id=data.get("protein_id"),
                protein_name=data.get("protein_name"),
                organism=data.get("organism"),
                accession=data.get("accession"),
                epath_gene_id=data.get("epath_gene_id"),
                epath_ko_id=data.get("epath_ko_id"),
                host_reference=data.get("host_reference"),
            )

            repository.session.commit()

            analysis = repository.find_by_id(analysis_id)

            job = AnalysisJob(
                analysis,
                app.config["ANALYSIS_QUEUE"],
            )

            app.config["ANALYSIS_QUEUE"].enqueue(job)

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
            "host_reference": analysis.host_reference,
            "report": analysis.report,
        }, 200

    @app.delete("/api/analyses/<analysis_id>")
    def delete_analysis(analysis_id):
        repository = app.config["ANALYSIS_REPOSITORY"]

        try:
            user_id = get_authenticated_user_id(request)
        except ValueError as error:
            return {"error": str(error)}, 401

        try:
            parsed_analysis_id = UUID(analysis_id)
        except ValueError:
            return {"error": "Invalid analysis ID."}, 400

        analysis = repository.find_by_id(parsed_analysis_id)

        if analysis is None:
            return {"error": "Analysis not found."}, 404

        if analysis.user_id != user_id:
            return {
                "error": "You do not have access to this analysis."
            }, 403

        if analysis.status in {"pending", "running"}:
            return {
                "error": (
                    "Cannot delete an analysis while it is pending or running."
                )
            }, 409

        try:
            repository.delete(parsed_analysis_id)
            repository.session.commit()
        except Exception:
            repository.session.rollback()
            app.logger.exception("Failed to delete analysis")
            return {"error": "Unable to delete analysis."}, 500

        return {
            "message": "Analysis deleted successfully.",
            "analysis_id": str(parsed_analysis_id),
        }, 200

    @app.get("/api/analyses/<analysis_id>/report.pdf")
    def download_analysis_report(analysis_id):
        repository = app.config["ANALYSIS_REPOSITORY"]

        try:
            user_id = get_authenticated_user_id(request)
        except ValueError as error:
            return {"error": str(error)}, 401

        try:
            parsed_analysis_id = UUID(analysis_id)
        except ValueError:
            return {"error": "Invalid analysis ID."}, 400

        analysis = repository.find_by_id(parsed_analysis_id)

        if analysis is None:
            return {"error": "Analysis not found."}, 404

        if analysis.user_id != user_id:
            return {
                "error": "You do not have access to this analysis."
            }, 403

        if analysis.status != "completed" or not analysis.report:
            return {
                "error": "A completed analysis report is required for export."
            }, 409

        try:
            pdf = generate_report_pdf(analysis.report)
        except (ValueError, TypeError) as error:
            app.logger.exception("Failed to generate analysis PDF")
            return {"error": "Unable to generate the analysis PDF."}, 500

        filename = f"analysis-{analysis.id}.pdf"

        return send_file(
            pdf,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=filename,
        ), 200

    @app.get("/api/health")
    def health():
        return {"status": "ok"}, 200

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