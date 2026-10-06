from app import (
    create_app,
    create_repository,
)
import io
import pytest
from app.repositories.analysis_repository import AnalysisRepository
from app.models.analysis_orm import AnalysisModel
from uuid import UUID

from app.services.analysis_worker import AnalysisWorker
from app.repositories.analysis_repository import AnalysisRepository
from app.services.token_service import create_token
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.services.password_service import hash_password
from app.models.user_orm import UserModel


def test_create_app_returns_flask_application():
    app = create_app()

    assert app is not None
    assert app.name == "app"

def test_analyze_endpoint_returns_protein_report(api_client, auth_headers):
    response = api_client.post(
        "/api/analyze",
        json={"sequence": "MKTIIALSYIFCLVFAD"},
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.get_json()

    assert "protein" in data
    assert "measurements" in data
    assert "evidence" in data
    assert "interpretations" in data
    assert "candidate_assessment" in data
    assert "limitations" in data

def test_analyze_endpoint_rejects_missing_json(api_client, auth_headers):

    response = api_client.post("/api/analyze", headers=auth_headers)

    assert response.status_code == 400

def test_analyze_endpoint_rejects_missing_sequence(api_client, auth_headers):
    response = api_client.post(
        "/api/analyze",
        json={"foo": "bar"},
        headers=auth_headers,
    )

    assert response.status_code == 400

def test_analyze_endpoint_rejects_empty_sequence(api_client, auth_headers):
    response = api_client.post(
        "/api/analyze",
        json={"sequence": ""},
        headers=auth_headers,
    )

    assert response.status_code == 400

def test_analyze_endpoint_rejects_invalid_sequence(api_client, auth_headers):
    response = api_client.post(
        "/api/analyze",
        json={"sequence": "MKTIIALSYIFCLVF1D"},
        headers=auth_headers,
    )

    assert response.status_code == 400

def test_analyze_endpoint_returns_error_for_invalid_sequence(api_client, auth_headers):
    response = api_client.post(
        "/api/analyze",
        json={"sequence": "MKTIIALSYIFCLVF1D"},
        headers=auth_headers,
    )

    assert response.status_code == 400

    data = response.get_json()

    assert "error" in data
    assert data["error"]

def test_analyze_endpoint_preserves_protein_id(api_client, auth_headers):
    response = api_client.post(
        "/api/analyze",
        json={
            "sequence": "MKTIIALSYIFCLVFAD",
            "protein_id": "protein_123",
        },
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["protein"]["id"] == "protein_123"

def test_analyze_endpoint_accepts_fasta_file(api_client, auth_headers):
    response = api_client.post(
        "/api/analyze",
        data={
            "file": (
                io.BytesIO(
                    b">protein_123\nMKTIIALSYIFCLVFAD\n"
                ),
                "protein.fasta",
            )
        },
        content_type="multipart/form-data",
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["protein"]["id"] == "protein_123"
    assert data["protein"]["sequence"] == "MKTIIALSYIFCLVFAD"

def test_analyze_endpoint_rejects_invalid_fasta_file(api_client, auth_headers):
    response = api_client.post(
        "/api/analyze",
        data={
            "file": (
                io.BytesIO(b"this is not fasta"),
                "protein.fasta",
            )
        },
        content_type="multipart/form-data",
        headers=auth_headers,
    )

    assert response.status_code == 400

    data = response.get_json()

    assert "error" in data
    assert data["error"]

def test_analyze_endpoint_rejects_empty_fasta_file(api_client, auth_headers):
    response = api_client.post(
        "/api/analyze",
        data={
            "file": (
                io.BytesIO(b""),
                "protein.fasta",
            )
        },
        content_type="multipart/form-data",
        headers=auth_headers,
    )

    assert response.status_code == 400

    data = response.get_json()

    assert "error" in data
    assert data["error"]

def test_analyze_endpoint_rejects_missing_fasta_file(api_client,auth_headers):
    response = api_client.post(
        "/api/analyze",
        data={},
        content_type="multipart/form-data",
        headers=auth_headers,
    )

    assert response.status_code == 400

    data = response.get_json()

    assert "error" in data
    assert data["error"]

def test_analyze_endpoint_accepts_multi_record_fasta_file(api_client, auth_headers):
    response = api_client.post(
        "/api/analyze",
        data={
            "file": (
                io.BytesIO(
                    b">protein_1\nMKTIIALSYIFCLVFAD\n"
                    b">protein_2\nMKTIIALSYIFCLVFAG\n"
                ),
                "proteins.fasta",
            )
        },
        content_type="multipart/form-data",
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.get_json()

    assert len(data["protein_analyses"]) == 2
    assert data["protein_analyses"][0]["protein_id"] == "protein_1"
    assert data["protein_analyses"][1]["protein_id"] == "protein_2"


def test_analyze_endpoint_preserves_protein_name(api_client, auth_headers):
    response = api_client.post(
        "/api/analyze",
        json={
            "sequence": "MKTIIALSYIFCLVFAD",
            "protein_id": "protein_1",
            "protein_name": "Example protein",
        },
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["protein"]["name"] == "Example protein"

def test_analyze_endpoint_preserves_organism(api_client, auth_headers):
    response = api_client.post(
        "/api/analyze",
        json={
            "sequence": "MKTIIALSYIFCLVFAD",
            "protein_id": "protein_1",
            "protein_name": "Example protein",
            "organism": "Example organism",
        },
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["protein"]["organism"] == "Example organism"


def test_analyze_endpoint_preserves_accession(api_client, auth_headers):
    response = api_client.post(
        "/api/analyze",
        json={
            "sequence": "MKTIIALSYIFCLVFAD",
            "protein_id": "protein_1",
            "protein_name": "Example protein",
            "organism": "Example organism",
            "accession": "ABC123",
        },
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["protein"]["accession"] == "ABC123"


def test_analyze_endpoint_preserves_fasta_description(api_client, auth_headers):
    response = api_client.post(
        "/api/analyze",
        data={
            "file": (
                io.BytesIO(
                    b">protein_123 Example protein\n"
                    b"MKTIIALSYIFCLVFAD\n"
                ),
                "protein.fasta",
            )
        },
        content_type="multipart/form-data",
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["protein"]["id"] == "protein_123"
    assert data["protein"]["name"] == "Example protein"


def test_analyze_endpoint_preserves_fasta_organism(api_client, auth_headers):
    response = api_client.post(
        "/api/analyze",
        data={
            "file": (
                io.BytesIO(
                    b">protein_123 Example protein OS=Escherichia coli\n"
                    b"MKTIIALSYIFCLVFAD\n"
                ),
                "protein.fasta",
            )
        },
        content_type="multipart/form-data",
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["protein"]["id"] == "protein_123"
    assert data["protein"]["name"] == "Example protein OS=Escherichia coli"
    assert data["protein"]["organism"] == "Escherichia coli"

def test_analyze_endpoint_preserves_fasta_accession(api_client, auth_headers):
    response = api_client.post(
        "/api/analyze",
        data={
            "file": (
                io.BytesIO(
                    b">sp|P12345|EXAMPLE_PROTEIN Example protein OS=Escherichia coli\n"
                    b"MKTIIALSYIFCLVFAD\n"
                ),
                "protein.fasta",
            )
        },
        content_type="multipart/form-data",
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["protein"]["id"] == "sp|P12345|EXAMPLE_PROTEIN"
    assert data["protein"]["accession"] == "P12345"

def test_analyze_endpoint_rejects_non_string_sequence(api_client, auth_headers):
    response = api_client.post(
        "/api/analyze",
        json={"sequence": 12345},
        headers=auth_headers,
    )

    assert response.status_code == 400

    data = response.get_json()

    assert "error" in data
    assert data["error"] == "Protein sequence must be a string."

def test_analyze_endpoint_rejects_null_sequence(api_client, auth_headers):
    response = api_client.post(
        "/api/analyze",
        json={"sequence": None},
        headers=auth_headers,
    )

    assert response.status_code == 400

    data = response.get_json()

    assert "error" in data
    assert data["error"] == "Protein sequence must be a string."

def test_analyze_endpoint_rejects_unsupported_content_type(api_client, auth_headers):
    response = api_client.post(
        "/api/analyze",
        data="MKTIIALSYIFCLVFAD",
        content_type="text/plain",
        headers=auth_headers,
    )

    assert response.status_code == 400

    data = response.get_json()

    assert data["error"] == "JSON request body is required."

def test_analyze_endpoint_rejects_malformed_json(api_client, auth_headers):
    response = api_client.post(
        "/api/analyze",
        data='{"sequence": ',
        content_type="application/json",
        headers=auth_headers,
    )

    assert response.status_code == 400

    data = response.get_json()

    assert data["error"] == "JSON request body is required."

def test_analyze_endpoint_rejects_fasta_file_without_filename(api_client, auth_headers):
    response = api_client.post(
        "/api/analyze",
        data={
            "file": (
                io.BytesIO(b">protein_123\nMKTIIALSYIFCLVFAD\n"),
                "",
            )
        },
        content_type="multipart/form-data",
        headers=auth_headers,
    )

    assert response.status_code == 400

    data = response.get_json()

    assert data["error"] == "FASTA file is required."

def test_analyze_endpoint_returns_consistent_error_structure_for_invalid_json(api_client, auth_headers):
    response = api_client.post(
        "/api/analyze",
        json={"sequence": "MKTIIALSYIFCLVF1D"},
        headers=auth_headers,
    )

    assert response.status_code == 400

    data = response.get_json()

    assert set(data) == {"error"}
    assert isinstance(data["error"], str)
    assert data["error"]

def test_analyze_endpoint_returns_stable_protein_response_structure(api_client, auth_headers):
    response = api_client.post(
        "/api/analyze",
        json={"sequence": "MKTIIALSYIFCLVFAD"},
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.get_json()

    assert set(data) == {
        "protein",
        "measurements",
        "peptide_candidates",
        "evidence",
        "interpretations",
        "candidate_assessment",
        "limitations",
        "conservation",
        "metadata",
    }

def test_analyze_endpoint_rejects_oversized_upload(auth_headers):
    app = create_app()
    app.config["MAX_CONTENT_LENGTH"] = 100

    client = app.test_client()

    response = client.post(
        "/api/analyze",
        data={
            "file": (
                io.BytesIO(
                    b">protein_123\n"
                    b"MKTIIALSYIFCLVFAD\n"
                ),
                "protein.fasta",
            )
        },
        content_type="multipart/form-data",
        headers=auth_headers,
    )

    assert response.status_code == 413

    data = response.get_json()

    assert data["error"]

def test_analyze_endpoint_rejects_unsupported_file_type(api_client, auth_headers):
    response = api_client.post(
        "/api/analyze",
        data={
            "file": (
                io.BytesIO(b">protein_123\nMKTIIALSYIFCLVFAD\n"),
                "protein.txt",
            )
        },
        content_type="multipart/form-data",
        headers=auth_headers,
    )

    assert response.status_code == 400

    data = response.get_json()

    assert data["error"] == "Unsupported file type. FASTA files are required."

@pytest.mark.parametrize(
    "filename",
    ["protein.fasta", "protein.fa", "protein.fna"],
)
def test_analyze_endpoint_accepts_supported_fasta_extensions(filename, api_client, auth_headers):
    response = api_client.post(
        "/api/analyze",
        data={
            "file": (
                io.BytesIO(
                    b">protein_123\n"
                    b"MKTIIALSYIFCLVFAD\n"
                ),
                filename,
            )
        },
        content_type="multipart/form-data",
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["protein"]["id"] == "protein_123"

@pytest.mark.parametrize(
    "filename",
    ["protein.FASTA", "protein.Fa", "protein.FNA"],
)
def test_analyze_endpoint_accepts_case_insensitive_fasta_extensions(filename, api_client, auth_headers):
    response = api_client.post(
        "/api/analyze",
        data={
            "file": (
                io.BytesIO(
                    b">protein_123\n"
                    b"MKTIIALSYIFCLVFAD\n"
                ),
                filename,
            )
        },
        content_type="multipart/form-data",
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["protein"]["id"] == "protein_123"

def test_analyze_v1_endpoint_returns_protein_report(api_client, auth_headers):
    response = api_client.post(
        "/api/v1/analyze",
        json={"sequence": "MKTIIALSYIFCLVFAD"},
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.get_json()

    assert "protein" in data
    assert "measurements" in data
    assert "evidence" in data
    assert "interpretations" in data
    assert "candidate_assessment" in data
    assert "limitations" in data
    assert "conservation" in data
    assert "metadata" in data

def test_analyze_endpoint_remains_available_after_api_versioning(api_client, auth_headers):
    response = api_client.post(
        "/api/analyze",
        json={"sequence": "MKTIIALSYIFCLVFAD"},
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.get_json()

    assert "protein" in data
    assert "measurements" in data
    assert "evidence" in data
    assert "interpretations" in data
    assert "candidate_assessment" in data
    assert "limitations" in data
    assert "conservation" in data
    assert "metadata" in data

def test_analyze_api_versions_return_equivalent_responses(api_client, auth_headers):
    payload = {"sequence": "MKTIIALSYIFCLVFAD"}

    legacy_response = api_client.post(
        "/api/analyze",
        headers=auth_headers,
        json=payload,
    )

    v1_response = api_client.post(
        "/api/v1/analyze",
        headers=auth_headers,
        json=payload,
    )

    assert legacy_response.status_code == 200
    assert v1_response.status_code == 200

    assert legacy_response.get_json() == v1_response.get_json()


def test_create_app_accepts_analysis_repository():
    repository = object()

    app = create_app(repository=repository)

    assert app is not None


def test_analyze_endpoint_uses_analysis_repository(auth_headers):
    class FakeSession:
        def commit(self):
            pass

        def rollback(self):
            pass


    class FakeRepository:
        def __init__(self):
            self.session = FakeSession()
            self.saved = []

        def save(self, analysis):
            self.saved.append(analysis)
            return analysis

    repository = FakeRepository()

    app = create_app(repository=repository)
    client = app.test_client()

    response = client.post(
        "/api/analyze",
        json={
            "sequence": "MKTIIALSYIFCLVFAD",
            "protein_id": "protein_123",
            "protein_name": "Example protein",
            "organism": "Example organism",
            "accession": "ABC123",
        },
        headers=auth_headers,
        
    )

    assert response.status_code == 200
    assert len(repository.saved) == 1

    saved = repository.saved[0]

    assert saved.protein_id == "protein_123"
    assert saved.protein_name == "Example protein"
    assert saved.organism == "Example organism"
    assert saved.accession == "ABC123"
    assert saved.sequence == "MKTIIALSYIFCLVFAD"


def test_create_app_builds_default_analysis_repository(monkeypatch):
    class FakeSession:
        pass

    class FakeSessionFactory:
        def __call__(self):
            return FakeSession()

    fake_session_factory = FakeSessionFactory()

    monkeypatch.setattr(
        "app.create_database_engine_from_environment",
        lambda: object(),
    )

    monkeypatch.setattr(
        "app.create_session_factory",
        lambda engine: fake_session_factory,
    )

    app = create_app()

    assert app.config["ANALYSIS_REPOSITORY"] is not None


def test_create_repository_builds_analysis_repository(monkeypatch):
    class FakeSession:
        pass

    class FakeSessionFactory:
        def __call__(self):
            return FakeSession()

    fake_session_factory = FakeSessionFactory()

    monkeypatch.setattr(
        "app.create_database_engine_from_environment",
        lambda: object(),
    )

    monkeypatch.setattr(
        "app.create_session_factory",
        lambda engine: fake_session_factory,
    )

    repository = create_repository()

    assert isinstance(repository, AnalysisRepository)


def test_analyze_endpoint_commits_successful_analysis(auth_headers):
    class FakeSession:
        def __init__(self):
            self.committed = False

        def commit(self):
            self.committed = True

    class FakeRepository:
        def __init__(self):
            self.session = FakeSession()
            self.saved = []

        def save(self, analysis):
            self.saved.append(analysis)
            return analysis

    repository = FakeRepository()
    app = create_app(repository=repository)
    client = app.test_client()

    response = client.post(
        "/api/analyze",
        json={"sequence": "MKTIIALSYIFCLVFAD"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert repository.session.committed is True

def test_analyze_endpoint_rolls_back_failed_analysis(auth_headers):
    class FakeSession:
        def __init__(self):
            self.rolled_back = False

        def commit(self):
            raise AssertionError("commit should not be called")

        def rollback(self):
            self.rolled_back = True

    class FakeRepository:
        def __init__(self):
            self.session = FakeSession()
            self.saved = []

        def save(self, analysis):
            self.saved.append(analysis)
            return analysis

    repository = FakeRepository()
    app = create_app(repository=repository)

    from unittest.mock import patch

    with patch(
        "app.run_analysis",
        side_effect=ValueError("analysis failed"),
    ):
        client = app.test_client()

        response = client.post(
            "/api/analyze",
            json={"sequence": "MKTIIALSYIFCLVFAD"},
            headers=auth_headers,
        )

    assert response.status_code == 400
    assert repository.session.rolled_back is True


def test_create_app_closes_default_repository_session(monkeypatch):
    class FakeSession:
        def __init__(self):
            self.closed = False

        def commit(self):
            pass

        def rollback(self):
            pass

        def close(self):
            self.closed = True

    class FakeRepository:
        def __init__(self):
            self.session = FakeSession()

        def save(self, analysis):
            return analysis

    repository = FakeRepository()

    monkeypatch.setattr(
        "app.create_repository",
        lambda: repository,
    )

    app = create_app()
    client = app.test_client()

    response = client.post(
        "/api/analyze",
        json={"sequence": "MKTIIALSYIFCLVFAD"},
    )

    assert response.status_code == 200
    assert repository.session.closed is True


def test_create_app_does_not_close_injected_repository_session():
    class FakeSession:
        def __init__(self):
            self.closed = False

        def commit(self):
            pass

        def rollback(self):
            pass

        def close(self):
            self.closed = True

    class FakeRepository:
        def __init__(self):
            self.session = FakeSession()

        def save(self, analysis):
            return analysis

    repository = FakeRepository()

    app = create_app(repository=repository)
    client = app.test_client()

    response = client.post(
        "/api/analyze",
        json={"sequence": "MKTIIALSYIFCLVFAD"},
    )

    assert response.status_code == 200
    assert repository.session.closed is False


def test_create_app_closes_default_repository_session_after_failure(monkeypatch):
    class FakeSession:
        def __init__(self):
            self.closed = False

        def commit(self):
            raise AssertionError("commit should not be called")

        def rollback(self):
            pass

        def close(self):
            self.closed = True

    class FakeRepository:
        def __init__(self):
            self.session = FakeSession()

        def save(self, analysis):
            return analysis

    repository = FakeRepository()

    monkeypatch.setattr(
        "app.create_repository",
        lambda: repository,
    )

    app = create_app()
    client = app.test_client()

    response = client.post(
        "/api/analyze",
        json={"sequence": "INVALID123"},
    )

    assert response.status_code == 400
    assert repository.session.closed is True

def test_api_client_uses_test_database_session(db_session):
    repository = AnalysisRepository(db_session)
    app = create_app(repository=repository)
    client = app.test_client()

    response = client.post(
        "/api/analyze",
        json={"sequence": "MKTIIALSYIFCLVFAD"},
    )

    assert response.status_code == 200

    analyses = db_session.query(AnalysisModel).all()

    assert len(analyses) == 1

def test_api_database_state_is_clean_after_previous_api_test(db_session):
    assert db_session.query(AnalysisModel).count() == 0



def test_submit_analysis_returns_pending_analysis(api_client, auth_token):
    response = api_client.post(
        "/api/analyses",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "sequence": "MKT",
            "protein_id": "P0A911",
            "protein_name": "Outer membrane protein A",
            "organism": "Escherichia coli O157:H7",
            "accession": "P0A911",
        },
    )

    assert response.status_code == 202

    data = response.get_json()

    assert "analysis_id" in data
    assert data["status"] == "pending"



def test_submit_analysis_requires_sequence(api_client, auth_token):
    response = api_client.post(
        "/api/analyses",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "protein_id": "P0A911",
        },
    )

    assert response.status_code == 400
    assert response.get_json() == {
        "error": "Sequence is required."
    }



def test_submit_analysis_requires_json_body(api_client, auth_token):
    response = api_client.post(
        "/api/analyses",
        headers={"Authorization": f"Bearer {auth_token}"},
        data="not-json",
        content_type="application/json",
    )

    assert response.status_code == 400
    assert response.get_json() == {
        "error": "JSON request body is required."
    }



def test_submit_analysis_handles_queue_failure(api_client, auth_token):
    class FailingQueue:
        def enqueue(self, job):
            raise RuntimeError("Queue unavailable")

    repository = api_client.application.config["ANALYSIS_REPOSITORY"]
    api_client.application.config["ANALYSIS_QUEUE"] = FailingQueue()

    response = api_client.post(
        "/api/analyses",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "sequence": "MKT",
            "protein_id": "P0A911",
        },
    )

    assert response.status_code == 500
    assert response.get_json() == {
        "error": "Queue unavailable"
    }



def test_submit_analysis_handles_persistence_failure(api_client, auth_token):
    class FailingRepository:
        def save(self, analysis):
            raise RuntimeError("Database unavailable")

        class Session:
            def rollback(self):
                pass

            def commit(self):
                pass

        session = Session()

    api_client.application.config["ANALYSIS_REPOSITORY"] = FailingRepository()

    response = api_client.post(
        "/api/analyses",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "sequence": "MKT",
            "protein_id": "P0A911",
        },
    )

    assert response.status_code == 500
    assert response.get_json() == {
        "error": "Database unavailable"
    }



def test_submit_analysis_commits_successful_submission(api_client, auth_token):
    repository = api_client.application.config["ANALYSIS_REPOSITORY"]

    response = api_client.post(
        "/api/analyses",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "sequence": "MKT",
            "protein_id": "P0A911",
        },
    )

    assert response.status_code == 202

    analysis_id = response.get_json()["analysis_id"]

    persisted = repository.find_by_id(analysis_id)

    assert persisted is not None
    assert persisted.status == "pending"



def test_get_analysis_status_returns_pending(api_client, auth_token):
    response = api_client.post(
        "/api/analyses",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "sequence": "MKT",
            "protein_id": "P0A911",
        },
    )

    assert response.status_code == 202

    analysis_id = response.get_json()["analysis_id"]

    response = api_client.get(f"/api/analyses/{analysis_id}", headers={"Authorization": f"Bearer {auth_token}"})

    assert response.status_code == 200

    data = response.get_json()

    assert data["analysis_id"] == analysis_id
    assert data["status"] == "pending"
    assert data["report"] is None



def test_get_analysis_status_returns_404_for_unknown_analysis(api_client, auth_token):
    response = api_client.get(
        "/api/analyses/00000000-0000-0000-0000-000000000000",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 404
    assert response.get_json() == {
        "error": "Analysis not found."
    }



def test_get_analysis_status_rejects_invalid_analysis_id(api_client, auth_token):
    response = api_client.get("/api/analyses/not-a-uuid",headers={"Authorization": f"Bearer {auth_token}"},)

    assert response.status_code == 400
    assert response.get_json() == {
        "error": "Invalid analysis ID."
    }



def test_get_analysis_status_returns_completed(api_client, auth_token):
    response = api_client.post(
        "/api/analyses",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "sequence": "MKT",
            "protein_id": "P0A911",
        },
    )

    assert response.status_code == 202

    analysis_id = response.get_json()["analysis_id"]

    repository = api_client.application.config["ANALYSIS_REPOSITORY"]
    analysis = repository.find_by_id(analysis_id)

    analysis.status = "completed"
    analysis.report = {
        "protein": {
            "id": "P0A911",
        },
        "sequence": "MKT",
        "length": 3,
    }
    repository.update(analysis)
    repository.session.commit()

    response = api_client.get(f"/api/analyses/{analysis_id}", headers={"Authorization": f"Bearer {auth_token}"},)

    assert response.status_code == 200

    data = response.get_json()

    assert data["analysis_id"] == analysis_id
    assert data["status"] == "completed"
    assert data["report"] == analysis.report



def test_get_analysis_status_returns_failed(api_client, auth_token):
    response = api_client.post(
        "/api/analyses",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "sequence": "MKT",
            "protein_id": "P0A911",
        },
    )

    assert response.status_code == 202

    analysis_id = response.get_json()["analysis_id"]

    repository = api_client.application.config["ANALYSIS_REPOSITORY"]
    analysis = repository.find_by_id(analysis_id)

    analysis.status = "failed"
    repository.update(analysis)
    repository.session.commit()

    response = api_client.get(f"/api/analyses/{analysis_id}", headers={"Authorization": f"Bearer {auth_token}"},)

    assert response.status_code == 200

    data = response.get_json()

    assert data["analysis_id"] == analysis_id
    assert data["status"] == "failed"



def test_analysis_submission_worker_and_status_lifecycle(api_client, auth_token):
    response = api_client.post(
        "/api/analyses",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "sequence": "MKT",
            "protein_id": "P0A911",
            "protein_name": "Outer membrane protein A",
            "organism": "Escherichia coli O157:H7",
            "accession": "P0A911",
        },
    )

    assert response.status_code == 202

    data = response.get_json()
    analysis_id = data["analysis_id"]

    assert data["status"] == "pending"

    repository = api_client.application.config["ANALYSIS_REPOSITORY"]
    analysis = repository.find_by_id(UUID(analysis_id))

    assert analysis is not None
    assert analysis.status == "pending"



def test_analysis_submission_worker_and_status_failure_lifecycle(api_client, auth_token):
    response = api_client.post(
        "/api/analyses",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "sequence": "MKT",
            "protein_id": "P0A911",
        },
    )

    assert response.status_code == 202

    analysis_id = response.get_json()["analysis_id"]

    repository = api_client.application.config["ANALYSIS_REPOSITORY"]
    analysis = repository.find_by_id(UUID(analysis_id))

    assert analysis is not None
    assert analysis.status == "pending"

def test_analysis_submission_commits_before_dispatching_task(
    api_client,
    auth_token,
    monkeypatch,
):
    order = []

    repository = api_client.application.config["ANALYSIS_REPOSITORY"]

    original_commit = repository.session.commit

    def tracked_commit():
        order.append("commit")
        return original_commit()

    def fake_delay(analysis_id):
        order.append("enqueue")

    monkeypatch.setattr(
        repository.session,
        "commit",
        tracked_commit,
    )

    monkeypatch.setattr(
        "app.services.celery_queue.execute_analysis_task.delay",
        fake_delay,
    )

    response = api_client.post(
        "/api/analyses",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "sequence": "MKT",
            "protein_id": "P0A911",
        },
    )

    assert response.status_code == 202
    assert order == ["commit", "enqueue"]

def test_login_returns_token(api_client, db_session):
    user = User(
        email="login@example.com",
        password_hash=hash_password("password123"),
    )

    user_repository = UserRepository(db_session)
    user_repository.save(user)
    db_session.commit()

    response = api_client.post(
        "/api/login",
        json={
            "email": "login@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["user_id"] == str(user.id)
    assert data["token"]

def test_login_rejects_unknown_email(api_client):
    response = api_client.post(
        "/api/login",
        json={
            "email": "unknown@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 401
    assert response.get_json() == {
        "error": "Invalid email or password."
    }

def test_login_rejects_incorrect_password(api_client, db_session):
    user = User(
        email="wrong-password@example.com",
        password_hash=hash_password("correct-password"),
    )

    user_repository = UserRepository(db_session)
    user_repository.save(user)
    db_session.commit()

    response = api_client.post(
        "/api/login",
        json={
            "email": "wrong-password@example.com",
            "password": "wrong-password",
        },
    )

    assert response.status_code == 401
    assert response.get_json() == {
        "error": "Invalid email or password."
    }

def test_login_requires_email_and_password(api_client):
    response = api_client.post(
        "/api/login",
        json={
            "email": "login@example.com",
        },
    )

    assert response.status_code == 400
    assert response.get_json() == {
        "error": "Email and password are required."
    }

def test_register_creates_user(api_client, db_session):
    response = api_client.post(
        "/api/register",
        json={
            "email": "newuser@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 201

    data = response.get_json()

    assert "user_id" in data
    assert data["user_id"]

    user = db_session.query(UserModel).filter_by(
        email="newuser@example.com"
    ).first()

    assert user is not None
    assert user.email == "newuser@example.com"

def test_register_requires_json_body(api_client):
    response = api_client.post("/api/register")

    assert response.status_code == 400
    assert response.get_json() == {
        "error": "JSON request body is required."
    }

def test_register_requires_email_and_password(api_client):
    response = api_client.post(
        "/api/register",
        json={
            "email": "newuser@example.com",
        },
    )

    assert response.status_code == 400
    assert response.get_json() == {
        "error": "Email and password are required."
    }

def test_register_rejects_duplicate_email(api_client):
    first_response = api_client.post(
        "/api/register",
        json={
            "email": "duplicate@example.com",
            "password": "password123",
        },
    )

    assert first_response.status_code == 201

    second_response = api_client.post(
        "/api/register",
        json={
            "email": "duplicate@example.com",
            "password": "anotherpassword123",
        },
    )

    assert second_response.status_code == 400
    assert second_response.get_json() == {
        "error": "Email is already registered."
    }

def test_register_does_not_store_plaintext_password(api_client, db_session):
    response = api_client.post(
        "/api/register",
        json={
            "email": "secure@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 201

    user = db_session.query(UserModel).filter_by(
        email="secure@example.com"
    ).first()

    assert user is not None
    assert user.password_hash != "password123"

def test_analyze_endpoint_requires_authentication(api_client):
    response = api_client.post(
        "/api/analyze",
        json={"sequence": "MKTIIALSYIFCLVFAD"},
    )

    assert response.status_code == 401
    assert response.get_json() == {
        "error": "Authentication required."
    }