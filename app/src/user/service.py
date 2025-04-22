from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status
import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.src.common.token import Token
from app.src.user import repository as user_repository
from app.src.user.dto.request.user_create_request import UserCreateRequest
from app.src.user.dto.response.user_create_response import UserCreateResponse

SECRET_KEY = "secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def register(db: Session, user: UserCreateRequest) -> UserCreateResponse:
    saved_user = user_repository.find_by_email(db, user.email)
    if saved_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="중복된 이메일 입니다."
        )

    user.password = _get_password_hash(user.password)
    created_user = user_repository.create(db, user.toModel())

    return UserCreateResponse.from_model(created_user)


def login(db: Session, email: str, password: str) -> Token:
    user = user_repository.find_by_email(db, email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="존재하지 않는 이메일 입니다.",
        )
    if not _verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="비밀번호가 일치하지 않습니다.",
        )

    return _create_access_token(data={"sub": user.email})


def _get_password_hash(password):
    return pwd_context.hash(password)


def _verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


# JWT 토큰 생성 함수
def _create_access_token(data: dict) -> Token:
    expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    expire = datetime.now(timezone.utc) + expires_delta
    data.update({"exp": expire})

    access_token = jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)
    return Token(access_token=access_token, token_type="bearer")
