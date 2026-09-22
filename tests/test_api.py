from app import create_app


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