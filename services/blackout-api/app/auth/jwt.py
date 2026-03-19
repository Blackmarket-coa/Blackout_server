from datetime import datetime, timedelta, timezone

import jwt as pyjwt

from app import config


def create_token(user_id: str, matrix_user_id: str, matrix_access_token: str) -> str:
    payload = {
        "sub": user_id,
        "matrix_user_id": matrix_user_id,
        "matrix_access_token": matrix_access_token,
        "exp": datetime.now(timezone.utc) + timedelta(hours=config.JWT_EXPIRY_HOURS),
        "iat": datetime.now(timezone.utc),
    }
    return pyjwt.encode(payload, config.JWT_SECRET, algorithm=config.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    return pyjwt.decode(token, config.JWT_SECRET, algorithms=[config.JWT_ALGORITHM])
