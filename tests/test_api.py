from app import (
    create_app,
    create_repository,
)
import io
import pytest
from app.repositories.analysis_repository import AnalysisRepository
from app.models.analysis_orm import AnalysisModel


def test_create_app_returns_flask_application():
    app = create_app()

    assert app is not None
    assert app.name == "app"

def test_analyze_endpoint_returns_protein_report(api_client):
    response = api_client.post(
        "/api/analyze",
        json={"sequence": "MKTIIALSYIFCLVFAD"},
    )

    assert response.status_code == 200

    data = response.get_json()

    assert "protein" in data
    assert "measurements" in data
    assert "evidence" in data
    assert "interpretations" in data
    assert "candidate_assessment" in data
    assert "limitations" in data

def test_analyze_endpoint_rejects_missing_json(api_client):

    response = api_client.post("/api/analyze")

    assert response.status_code == 400

def test_analyze_endpoint_rejects_missing_sequence(api_client):
    response = api_client.post(
        "/api/analyze",
        json={"foo": "bar"},
    )

    assert response.status_code == 400

def test_analyze_endpoint_rejects_empty_sequence(api_client):
    response = api_client.post(
        "/api/analyze",
        json={"sequence": ""},
    )

    assert response.status_code == 400

def test_analyze_endpoint_rejects_invalid_sequence(api_client):
    response = api_client.post(
        "/api/analyze",
        json={"sequence": "MKTIIALSYIFCLVF1D"},
    )

    assert response.status_code == 400

def test_analyze_endpoint_returns_error_for_invalid_sequence(api_client):
    response = api_client.post(
        "/api/analyze",
        json={"sequence": "MKTIIALSYIFCLVF1D"},
    )

    assert response.status_code == 400

    data = response.get_json()

    assert "error" in data
    assert data["error"]

def test_analyze_endpoint_preserves_protein_id(api_client):
    response = api_client.post(
        "/api/analyze",
        json={
            "sequence": "MKTIIALSYIFCLVFAD",
            "protein_id": "protein_123",
        },
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["protein"]["id"] == "protein_123"

def test_analyze_endpoint_accepts_fasta_file(api_client):
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
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["protein"]["id"] == "protein_123"
    assert data["protein"]["sequence"] == "MKTIIALSYIFCLVFAD"

def test_analyze_endpoint_rejects_invalid_fasta_file(api_client):
    response = api_client.post(
        "/api/analyze",
        data={
            "file": (
                io.BytesIO(b"this is not fasta"),
                "protein.fasta",
            )
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 400

    data = response.get_json()

    assert "error" in data
    assert data["error"]

def test_analyze_endpoint_rejects_empty_fasta_file(api_client):
    response = api_client.post(
        "/api/analyze",
        data={
            "file": (
                io.BytesIO(b""),
                "protein.fasta",
            )
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 400

    data = response.get_json()

    assert "error" in data
    assert data["error"]

def test_analyze_endpoint_rejects_missing_fasta_file(api_client):
    response = api_client.post(
        "/api/analyze",
        data={},
        content_type="multipart/form-data",
    )

    assert response.status_code == 400

    data = response.get_json()

    assert "error" in data
    assert data["error"]

def test_analyze_endpoint_accepts_multi_record_fasta_file(api_client):
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
    )

    assert response.status_code == 200

    data = response.get_json()

    assert len(data["protein_analyses"]) == 2
    assert data["protein_analyses"][0]["protein_id"] == "protein_1"
    assert data["protein_analyses"][1]["protein_id"] == "protein_2"


def test_analyze_endpoint_preserves_protein_name(api_client):
    response = api_client.post(
        "/api/analyze",
        json={
            "sequence": "MKTIIALSYIFCLVFAD",
            "protein_id": "protein_1",
            "protein_name": "Example protein",
        },
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["protein"]["name"] == "Example protein"

def test_analyze_endpoint_preserves_organism(api_client):
    response = api_client.post(
        "/api/analyze",
        json={
            "sequence": "MKTIIALSYIFCLVFAD",
            "protein_id": "protein_1",
            "protein_name": "Example protein",
            "organism": "Example organism",
        },
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["protein"]["organism"] == "Example organism"


def test_analyze_endpoint_preserves_accession(api_client):
    response = api_client.post(
        "/api/analyze",
        json={
            "sequence": "MKTIIALSYIFCLVFAD",
            "protein_id": "protein_1",
            "protein_name": "Example protein",
            "organism": "Example organism",
            "accession": "ABC123",
        },
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["protein"]["accession"] == "ABC123"


def test_analyze_endpoint_preserves_fasta_description(api_client):
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
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["protein"]["id"] == "protein_123"
    assert data["protein"]["name"] == "Example protein"


def test_analyze_endpoint_preserves_fasta_organism(api_client):
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
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["protein"]["id"] == "protein_123"
    assert data["protein"]["name"] == "Example protein OS=Escherichia coli"
    assert data["protein"]["organism"] == "Escherichia coli"

def test_analyze_endpoint_preserves_fasta_accession(api_client):
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
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["protein"]["id"] == "sp|P12345|EXAMPLE_PROTEIN"
    assert data["protein"]["accession"] == "P12345"

def test_analyze_endpoint_rejects_non_string_sequence(api_client):
    response = api_client.post(
        "/api/analyze",
        json={"sequence": 12345},
    )

    assert response.status_code == 400

    data = response.get_json()

    assert "error" in data
    assert data["error"] == "Protein sequence must be a string."

def test_analyze_endpoint_rejects_null_sequence(api_client):
    response = api_client.post(
        "/api/analyze",
        json={"sequence": None},
    )

    assert response.status_code == 400

    data = response.get_json()

    assert "error" in data
    assert data["error"] == "Protein sequence must be a string."

def test_analyze_endpoint_rejects_unsupported_content_type(api_client):
    response = api_client.post(
        "/api/analyze",
        data="MKTIIALSYIFCLVFAD",
        content_type="text/plain",
    )

    assert response.status_code == 400

    data = response.get_json()

    assert data["error"] == "JSON request body is required."

def test_analyze_endpoint_rejects_malformed_json(api_client):
    response = api_client.post(
        "/api/analyze",
        data='{"sequence": ',
        content_type="application/json",
    )

    assert response.status_code == 400

    data = response.get_json()

    assert data["error"] == "JSON request body is required."

def test_analyze_endpoint_rejects_fasta_file_without_filename(api_client):
    response = api_client.post(
        "/api/analyze",
        data={
            "file": (
                io.BytesIO(b">protein_123\nMKTIIALSYIFCLVFAD\n"),
                "",
            )
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 400

    data = response.get_json()

    assert data["error"] == "FASTA file is required."

def test_analyze_endpoint_returns_consistent_error_structure_for_invalid_json(api_client):
    response = api_client.post(
        "/api/analyze",
        json={"sequence": "MKTIIALSYIFCLVF1D"},
    )

    assert response.status_code == 400

    data = response.get_json()

    assert set(data) == {"error"}
    assert isinstance(data["error"], str)
    assert data["error"]

def test_analyze_endpoint_returns_stable_protein_response_structure(api_client):
    response = api_client.post(
        "/api/analyze",
        json={"sequence": "MKTIIALSYIFCLVFAD"},
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

def test_analyze_endpoint_rejects_oversized_upload():
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
    )

    assert response.status_code == 413

    data = response.get_json()

    assert data["error"]

def test_analyze_endpoint_rejects_unsupported_file_type(api_client):
    response = api_client.post(
        "/api/analyze",
        data={
            "file": (
                io.BytesIO(b">protein_123\nMKTIIALSYIFCLVFAD\n"),
                "protein.txt",
            )
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 400

    data = response.get_json()

    assert data["error"] == "Unsupported file type. FASTA files are required."

@pytest.mark.parametrize(
    "filename",
    ["protein.fasta", "protein.fa", "protein.fna"],
)
def test_analyze_endpoint_accepts_supported_fasta_extensions(filename, api_client):
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
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["protein"]["id"] == "protein_123"

@pytest.mark.parametrize(
    "filename",
    ["protein.FASTA", "protein.Fa", "protein.FNA"],
)
def test_analyze_endpoint_accepts_case_insensitive_fasta_extensions(filename, api_client):
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
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["protein"]["id"] == "protein_123"

def test_analyze_v1_endpoint_returns_protein_report(api_client):
    response = api_client.post(
        "/api/v1/analyze",
        json={"sequence": "MKTIIALSYIFCLVFAD"},
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

def test_analyze_endpoint_remains_available_after_api_versioning(api_client):
    response = api_client.post(
        "/api/analyze",
        json={"sequence": "MKTIIALSYIFCLVFAD"},
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

def test_analyze_api_versions_return_equivalent_responses(api_client):
    payload = {"sequence": "MKTIIALSYIFCLVFAD"}

    legacy_response = api_client.post(
        "/api/analyze",
        json=payload,
    )

    v1_response = api_client.post(
        "/api/v1/analyze",
        json=payload,
    )

    assert legacy_response.status_code == 200
    assert v1_response.status_code == 200

    assert legacy_response.get_json() == v1_response.get_json()


def test_create_app_accepts_analysis_repository():
    repository = object()

    app = create_app(repository=repository)

    assert app is not None


def test_analyze_endpoint_uses_analysis_repository():
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


def test_analyze_endpoint_commits_successful_analysis():
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
    )

    assert response.status_code == 200
    assert repository.session.committed is True

def test_analyze_endpoint_rolls_back_failed_analysis():
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
