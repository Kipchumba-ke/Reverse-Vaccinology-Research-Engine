import os
from uuid import UUID

import jwt


def create_token(user) -> str:
    secret_key = os.environ["JWT_SECRET_KEY"]

    payload = {
        "sub": str(user.id),
    }

    return jwt.encode(
        payload,
        secret_key,
        algorithm="HS256",
    )

def decode_token(token: str) -> UUID:
    secret_key = os.environ["JWT_SECRET_KEY"]

    payload = jwt.decode(
        token,
        secret_key,
        algorithms=["HS256"],
    )

    return UUID(payload["sub"])