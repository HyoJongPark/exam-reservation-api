from typing import Annotated, List
from fastapi import APIRouter, Body, Depends, Query
from sqlalchemy.orm import Session

from app.src.config.database import get_db_from_request
from app.src.middleware.authenticate import authenticate_admin, authenticate_user
from app.src.reservation.dto.request.create_reservation_request import (
    CreateReservationRequest,
)
from app.src.reservation import service as reservation_service
from app.src.reservation.dto.request.get_available_schedule_request import (
    GetAvailableScheduleRequest,
)
from app.src.reservation.dto.request.get_reservations_request import (
    GetReservationsRequest,
)
from app.src.reservation.dto.request.update_reservation_request import (
    UpdateReservationRequest,
)
from app.src.reservation.dto.response.get_available_schedule_response import (
    GetAvailableScheduleResponse,
)
from app.src.reservation.dto.response.reservation_response import ReservationResponse
from app.src.user.model import User


router = APIRouter(prefix="/reservations", tags=["reservations"])


@router.get("", response_model=List[ReservationResponse])
def get_reservations(
    user: Annotated[User, Depends(authenticate_user)],
    request: Annotated[GetReservationsRequest, Query()],
    db: Session = Depends(get_db_from_request),
) -> List[ReservationResponse]:
    return reservation_service.find_all_by_date(db, user, request)


@router.get("/{reservation_id}", response_model=ReservationResponse)
def get_reservation(
    user: Annotated[User, Depends(authenticate_user)],
    reservation_id: int,
    db: Session = Depends(get_db_from_request),
) -> ReservationResponse:
    return reservation_service.find_by_id(db, user, reservation_id)


@router.get("/schedules", response_model=List[GetAvailableScheduleResponse])
def get_available_schedules(
    user: Annotated[User, Depends(authenticate_user)],
    request: Annotated[GetAvailableScheduleRequest, Query()],
    db: Session = Depends(get_db_from_request),
) -> List[GetAvailableScheduleResponse]:
    return reservation_service.find_available_schedules(db, request)


@router.post("/", response_model=ReservationResponse)
def create_reservation(
    user: Annotated[User, Depends(authenticate_user)],
    request: Annotated[CreateReservationRequest, Body()],
    db: Session = Depends(get_db_from_request),
) -> ReservationResponse:
    print("request.end_time", request.end_time)
    return reservation_service.create_reservation(db, user, request)


@router.post("/{reservation_id}/confirm", response_model=ReservationResponse)
def confirm_reservation(
    user: Annotated[User, Depends(authenticate_admin)],
    reservation_id: int,
    db: Session = Depends(get_db_from_request),
) -> ReservationResponse:
    return reservation_service.confirm_reservation(db, user, reservation_id)


@router.patch("/{reservation_id}", response_model=ReservationResponse)
def update_reservation(
    user: Annotated[User, Depends(authenticate_user)],
    reservation_id: int,
    request: Annotated[UpdateReservationRequest, Body()],
    db: Session = Depends(get_db_from_request),
) -> ReservationResponse:
    return reservation_service.update_reservation(db, user, reservation_id, request)
