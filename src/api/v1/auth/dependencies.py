from functools import lru_cache

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from src.config import settings


@lru_cache()
def get_public_key() -> str:
    return settings.auth_jwt.public_key_path.read_text()


security = HTTPBearer()


async def verify_service_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    try:
        jwt.decode(
            credentials.credentials,
            get_public_key(),
            algorithms=[settings.auth_jwt.algorithm],
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return True
