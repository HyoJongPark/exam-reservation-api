from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from sqlalchemy.orm import Session

from app.src.common.token import TokenData
from app.src.config.database import get_db_from_request
from app.src.user import repository as user_repository
from app.src.user.model import Role


SECRET_KEY = "secret_key"
ALGORITHM = "HS256"

security = HTTPBearer(auto_error=False)


def _decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )
        return TokenData(email=email)
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        ) from e


async def authenticate_user(
    db: Session = Depends(get_db_from_request),
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)] = None,
):
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header is missing or invalid",
        )
    token_data = _decode_token(credentials.credentials)
    user = user_repository.find_by_email(db, token_data.email)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
    return user


async def authenticate_admin(
    db: Session = Depends(get_db_from_request),
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)] = None,
):
    user = await authenticate_user(db, credentials)
    if user.role != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="관리자 권한이 필요합니다."
        )
    return user
