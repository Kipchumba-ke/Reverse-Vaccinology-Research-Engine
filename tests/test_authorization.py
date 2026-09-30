from app.services.token_service import create_token
from app.models.user import User



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
