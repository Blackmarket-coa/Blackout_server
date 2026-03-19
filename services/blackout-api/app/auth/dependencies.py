from dataclasses import dataclass

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.jwt import decode_token

_bearer = HTTPBearer()


@dataclass
class CurrentUser:
    id: str
    matrix_user_id: str
    matrix_access_token: str


async def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(_bearer),
) -> CurrentUser:
    try:
        payload = decode_token(creds.credentials)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    return CurrentUser(
        id=payload["sub"],
        matrix_user_id=payload["matrix_user_id"],
        matrix_access_token=payload["matrix_access_token"],
    )
