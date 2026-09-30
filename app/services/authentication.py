import jwt

from app.services.token_service import decode_token


def get_authenticated_user_id(request):
    authorization = request.headers.get("Authorization")

    if not authorization:
        raise ValueError("Authentication required.")

    if not authorization.startswith("Bearer "):
        raise ValueError("Invalid authentication token.")

    token = authorization.removeprefix("Bearer ")

    try:
        return decode_token(token)
    except jwt.InvalidTokenError as error:
        raise ValueError("Invalid authentication token.") from error