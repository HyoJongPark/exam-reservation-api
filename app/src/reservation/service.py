import datetime
from typing import List
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.src.reservation.dto.request.create_reservation_request import (
    CreateReservationRequest,
)
from app.src.reservation.dto.request.get_available_schedule_request import (
    GetAvailableScheduleRequest,
)
from app.src.reservation.dto.response.get_available_schedule_response import (
    GetAvailableScheduleResponse,
)
from app.src.reservation.dto.response.reservation_response import ReservationResponse
from app.src.reservation import repository as reservation_repository
from app.src.reservation.model import Reservation, ReservationStatus
from app.src.reservation.utils.constants import (
    MAX_CAPACITY,
    SLOT_MINUTES,
)
from app.src.user.model import User


def find_available_schedules(
    db: Session, request: GetAvailableScheduleRequest
) -> List[GetAvailableScheduleResponse]:
    reservations = reservation_repository.find_all_by_range_and_status(
        db, request.start_time, request.end_time, [ReservationStatus.CONFIRMED], False
    )

    schedules = _generate_slots_with_reservation(
        start_date=request.start_time,
        end_date=request.end_time,
        reservations=reservations,
    )
    return _merge_schedules(schedules)


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
    reservations = reservation_repository.find_all_by_range_and_status(
        db,
        start_time,
        end_time,
        [ReservationStatus.PENDING, ReservationStatus.CONFIRMED],
        lock,
    )

    # 슬롯별로 누적된 예약 수를 가져온다
    schedules = _generate_slots_with_reservation(start_time, end_time, reservations)

    # 슬롯 중 하나라도 5만명 초과되는지 체크
    for schedule in schedules:
        if schedule.available_capacity - number_of_people < 0:
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
    # 1. 스케줄 객체로 초기화
    total_minutes = int((end_date - start_date).total_seconds() // 60) // SLOT_MINUTES
    schedules = []
    for idx in range(total_minutes):
        slot_start = start_date + datetime.timedelta(minutes=idx * SLOT_MINUTES)
        slot_end = slot_start + datetime.timedelta(minutes=SLOT_MINUTES)
        schedules.append(
            GetAvailableScheduleResponse(
                start_time=slot_start,
                end_time=slot_end,
                available_capacity=MAX_CAPACITY,
            )
        )

    # 2. 예약을 스케줄 인덱스에 반영
    for res in reservations:
        if res.status == ReservationStatus.PENDING:
            continue

        start_diff = (res.start_time - start_date).total_seconds() // 60
        end_diff = (res.end_time - start_date).total_seconds() // 60

        start_idx = int(start_diff // SLOT_MINUTES)
        end_idx = min(len(schedules), int((end_diff + SLOT_MINUTES) // SLOT_MINUTES))

        for idx in range(start_idx, end_idx):
            schedules[idx].available_capacity -= res.number_of_people

    return schedules


def _merge_schedules(
    schedules: List[GetAvailableScheduleResponse],
) -> List[GetAvailableScheduleResponse]:
    """
    예약이 불가한 스케줄을 필터링하고, 예약 가능 인원이 동일한 연속 구간을 병합
    """
    if len(schedules) == 0:
        return []

    schedules = [schedule for schedule in schedules if schedule.available_capacity > 0]

    merged = []
    current = schedules[0]
    for next_schedule in schedules[1:]:
        if (
            current.end_time == next_schedule.start_time
            and current.available_capacity == next_schedule.available_capacity
        ):
            current.end_time = next_schedule.end_time
            continue

        merged.append(current)
        current = next_schedule
    merged.append(current)

    return merged
