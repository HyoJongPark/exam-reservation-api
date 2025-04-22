from typing import Annotated
from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session

from app.src.config.database import get_db_from_request
from app.src.middleware.authenticate import authenticate_user
from app.src.reservation.dto.request.create_reservation_request import (
    CreateReservationRequest,
)
from app.src.reservation import service as reservation_service
from app.src.user.model import User


router = APIRouter(prefix="/reservations", tags=["reservations"])


# 완료
@router.post("/")
def create_reservation(
    user: Annotated[User, Depends(authenticate_user)],
    request: Annotated[CreateReservationRequest, Body()],
    db: Session = Depends(get_db_from_request),
):
    print("request.end_time", request.end_time)
    return reservation_service.create_reservation(db, user, request)
