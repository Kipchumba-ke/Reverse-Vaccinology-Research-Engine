from uuid import UUID
from flask import request

from app.repositories.analysis_repository import AnalysisRepository
from app.services.token_service import create_token
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.services.authentication import get_authenticated_user_id



def test_protected_request_requires_authorization_header(api_client):
    response = api_client.get("/api/protected")

    assert response.status_code == 401


def test_protected_request_rejects_invalid_token(api_client):
    response = api_client.get(
        "/api/protected",
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert response.status_code == 401


def test_protected_request_accepts_valid_token(api_client):
    user = User(
        email="protected@example.com",
        password_hash="hashed-password",
    )

    token = create_token(user)

    response = api_client.get(
        "/api/protected",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json["user_id"] == str(user.id)


def test_user_can_access_own_analysis(api_client, db_session):
    user = User(
        email="owner@example.com",
        password_hash="hashed-password",
    )

    user_repository = UserRepository(db_session)
    user_repository.save(user)
    db_session.commit()

    token = create_token(user)

    response = api_client.post(
        "/api/analyses",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "protein_id": "P001",
            "protein_name": "Test Protein",
            "organism": "Test Organism",
            "sequence": "MKTAYIAKQRQISFVKSHFSRQ",
        },
    )

    assert response.status_code == 202

    analysis_id = response.json["analysis_id"]

    response = api_client.get(
        f"/api/analyses/{analysis_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

def test_user_cannot_access_another_users_analysis(api_client, db_session):
    owner = User(
        email="owner@example.com",
        password_hash="hashed-password",
    )

    other_user = User(
        email="other@example.com",
        password_hash="hashed-password",
    )

    user_repository = UserRepository(db_session)
    user_repository.save(owner)
    user_repository.save(other_user)
    db_session.commit()

    owner_token = create_token(owner)
    other_user_token = create_token(other_user)

    response = api_client.post(
        "/api/analyses",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={
            "protein_id": "P001",
            "protein_name": "Test Protein",
            "organism": "Test Organism",
            "sequence": "MKTAYIAKQRQISFVKSHFSRQ",
        },
    )

    assert response.status_code == 202

    analysis_id = response.json["analysis_id"]

    response = api_client.get(
        f"/api/analyses/{analysis_id}",
        headers={"Authorization": f"Bearer {other_user_token}"},
    )

    assert response.status_code == 403

def test_analysis_submission_assigns_authenticated_user_as_owner(
    api_client,
    db_session,
):
    user = User(
        email="owner@example.com",
        password_hash="hashed-password",
    )

    user_repository = UserRepository(db_session)
    user_repository.save(user)
    db_session.commit()

    token = create_token(user)

    response = api_client.post(
        "/api/analyses",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "protein_id": "P001",
            "protein_name": "Test Protein",
            "organism": "Test Organism",
            "sequence": "MKTAYIAKQRQISFVKSHFSRQ",
        },
    )

    assert response.status_code == 202

    analysis_id = response.json["analysis_id"]

    analysis_repository = AnalysisRepository(db_session)
    analysis = analysis_repository.find_by_id(
        UUID(analysis_id)
    )

    assert analysis.user_id == user.id

def test_analysis_status_requires_authentication(api_client):
    response = api_client.get(
        "/api/analyses/00000000-0000-0000-0000-000000000000"
    )

    assert response.status_code == 401

def test_authentication_helper_extracts_user_id(api_client):
    user = User(
        email="helper@example.com",
        password_hash="hashed-password",
    )

    token = create_token(user)

    with api_client.application.test_request_context(
        headers={"Authorization": f"Bearer {token}"}
    ):
        authenticated_user_id = get_authenticated_user_id(request)

    assert authenticated_user_id == user.id
