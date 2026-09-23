from app import create_app
import io


def test_create_app_returns_flask_application():
    app = create_app()

    assert app is not None
    assert app.name == "app"

def test_analyze_endpoint_returns_protein_report():
    app = create_app()
    client = app.test_client()

    response = client.post(
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

def test_analyze_endpoint_rejects_missing_json():
    app = create_app()
    client = app.test_client()

    response = client.post("/api/analyze")

    assert response.status_code == 400

def test_analyze_endpoint_rejects_missing_sequence():
    app = create_app()
    client = app.test_client()

    response = client.post(
        "/api/analyze",
        json={"foo": "bar"},
    )

    assert response.status_code == 400

def test_analyze_endpoint_rejects_empty_sequence():
    app = create_app()
    client = app.test_client()

    response = client.post(
        "/api/analyze",
        json={"sequence": ""},
    )

    assert response.status_code == 400

def test_analyze_endpoint_rejects_invalid_sequence():
    app = create_app()
    client = app.test_client()

    response = client.post(
        "/api/analyze",
        json={"sequence": "MKTIIALSYIFCLVF1D"},
    )

    assert response.status_code == 400

def test_analyze_endpoint_returns_error_for_invalid_sequence():
    app = create_app()
    client = app.test_client()

    response = client.post(
        "/api/analyze",
        json={"sequence": "MKTIIALSYIFCLVF1D"},
    )

    assert response.status_code == 400

    data = response.get_json()

    assert "error" in data
    assert data["error"]

def test_analyze_endpoint_preserves_protein_id():
    app = create_app()
    client = app.test_client()

    response = client.post(
        "/api/analyze",
        json={
            "sequence": "MKTIIALSYIFCLVFAD",
            "protein_id": "protein_123",
        },
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["protein"]["id"] == "protein_123"

def test_analyze_endpoint_accepts_fasta_file():
    app = create_app()
    client = app.test_client()

    response = client.post(
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

def test_analyze_endpoint_rejects_invalid_fasta_file():
    app = create_app()
    client = app.test_client()

    response = client.post(
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

def test_analyze_endpoint_rejects_empty_fasta_file():
    app = create_app()
    client = app.test_client()

    response = client.post(
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

def test_analyze_endpoint_rejects_missing_fasta_file():
    app = create_app()
    client = app.test_client()

    response = client.post(
        "/api/analyze",
        data={},
        content_type="multipart/form-data",
    )

    assert response.status_code == 400

    data = response.get_json()

    assert "error" in data
    assert data["error"]

def test_analyze_endpoint_accepts_multi_record_fasta_file():
    app = create_app()
    client = app.test_client()

    response = client.post(
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


def test_analyze_endpoint_preserves_protein_name():
    app = create_app()
    client = app.test_client()

    response = client.post(
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

def test_analyze_endpoint_preserves_organism():
    app = create_app()
    client = app.test_client()

    response = client.post(
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


def test_analyze_endpoint_preserves_accession():
    app = create_app()
    client = app.test_client()

    response = client.post(
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