from app.integrations import alphafold


def test_structure_requires_authentication(api_client):
    response = api_client.get("/api/structure/P0A911")

    assert response.status_code == 401


def test_structure_returns_the_model(api_client, auth_headers, monkeypatch):
    monkeypatch.setattr(
        alphafold, "fetch_structure",
        lambda accession: {"accession": accession, "pdb": "ATOM"},
    )

    response = api_client.get("/api/structure/P0A911", headers=auth_headers)

    assert response.status_code == 200
    assert response.get_json()["accession"] == "P0A911"


def test_structure_maps_errors_to_status_codes(
    api_client, auth_headers, monkeypatch
):
    def raising(error):
        def fetch(accession):
            raise error
        return fetch

    cases = [
        (ValueError("bad accession"), 400),
        (alphafold.StructureNotFound("none"), 404),
        (RuntimeError("upstream"), 502),
    ]

    for error, status in cases:
        monkeypatch.setattr(alphafold, "fetch_structure", raising(error))
        response = api_client.get(
            "/api/structure/P0A911", headers=auth_headers
        )
        assert response.status_code == status
