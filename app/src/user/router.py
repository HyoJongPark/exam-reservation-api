from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.src.common.token import Token
from app.src.config.database import get_db_from_request
from app.src.user.dto.request.user_create_request import UserCreateRequest
from app.src.user.dto.request.user_login_request import UserLoginRequest
from app.src.user.dto.response.user_create_response import UserCreateResponse
from app.src.user import service as user_service


router = APIRouter(prefix="/users", tags=["users"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(
    request: UserCreateRequest, db: Session = Depends(get_db_from_request)
) -> UserCreateResponse:
    return user_service.register(db, request)


@router.post("/login")
def login(
    request: UserLoginRequest, db: Session = Depends(get_db_from_request)
) -> Token:
    return user_service.login(db, request)
