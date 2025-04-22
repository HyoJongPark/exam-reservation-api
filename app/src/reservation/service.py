import datetime
from typing import List
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.src.reservation.dto.request.create_reservation_request import (
    CreateReservationRequest,
)
from app.src.reservation.dto.response.reservation_response import ReservationResponse
from app.src.reservation import repository as reservation_repository
from app.src.reservation.model import Reservation
from app.src.reservation.utils.constants import (
    MAX_CAPACITY,
    SECONDS_PER_MINUTE,
    SLOT_MINUTES,
)
from app.src.user.model import User


def create_reservation(
    db: Session, user: User, request: CreateReservationRequest
) -> ReservationResponse:
    _validate_reservation_datetime(
        db, request.start_time, request.end_time, request.number_of_people
    )

    reservation = reservation_repository.create(db, request.toModel(user))
    return ReservationResponse.from_model(reservation)


def _validate_reservation_datetime(
    db: Session,
    start_time: datetime,
    end_time: datetime,
    number_of_people: int,
    lock: bool = False,
):
    """
    해당 시간 대에서 5만명이 넘는지 검사하는 함수

    - 동일한 구간에 시험이 치뤄지는 경우, 예약 가능 인원을 초과하는지 검사
    - 예약하려는 시간대와 겹치는 예약 전체 조회
    - 각 예약을 10분 단위의 슬롯으로 나눠서 구간 별로 5만명이 초과하는지 검사함
    - 이 조회 데이터는 검증 후 5만명이 초과되는 상황 방지를 위해 update lock 을 통해 관리될 수 있음(db.commit 이전까지)
    """
    reservations = reservation_repository.find_all_by_range(
        db, start_time, end_time, lock
    )

    # 슬롯별로 누적된 예약 수를 가져온다
    schedules = _generate_slots_with_reservation(start_time, end_time, reservations)

    # 슬롯 중 하나라도 5만명 초과되는지 체크
    for schedule in schedules:
        if schedule + number_of_people > MAX_CAPACITY:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="예약 가능 인원을 초과했습니다.",
            )


def _generate_slots_with_reservation(
    start_date: datetime,
    end_date: datetime,
    reservations: List[Reservation],
) -> List[int]:
    """
    예약 가능 시간 조회는 10분단위 조회가 가능
    시작/종료 일자 범위를 10분 단위로 나누고, 각 예약이 차지하는 슬롯을 카운트
    """
    slots = [0] * int(
        (end_date - start_date).total_seconds() // SECONDS_PER_MINUTE // SLOT_MINUTES
    )

    # 1. 예약을 슬롯 인덱스에 반영
    for res in reservations:
        start_diff = (res.start_time - start_date).total_seconds() // SECONDS_PER_MINUTE
        end_diff = (res.end_time - start_date).total_seconds() // SECONDS_PER_MINUTE

        start_idx = int(start_diff // SLOT_MINUTES)
        end_idx = min(len(slots), int((end_diff + SLOT_MINUTES) // SLOT_MINUTES))

        for idx in range(start_idx, end_idx):
            slots[idx] += res.number_of_people
    return slots
