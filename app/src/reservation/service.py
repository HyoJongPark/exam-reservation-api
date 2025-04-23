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
from app.src.reservation.dto.request.get_reservations_request import (
    GetReservationsRequest,
)
from app.src.reservation.dto.request.update_reservation_request import (
    UpdateReservationRequest,
)
from app.src.reservation.dto.response.get_available_schedule_response import (
    GetAvailableScheduleResponse,
)
from app.src.reservation import repository as reservation_repository
from app.src.reservation.model import Reservation, ReservationStatus
from app.src.reservation.utils.constants import (
    MAX_CAPACITY,
    SLOT_MINUTES,
)
from app.src.user.model import Role, User


def find_all_by_date(
    db: Session, user: User, request: GetReservationsRequest
) -> List[Reservation]:
    if user.role == Role.ADMIN:
        return reservation_repository.find_all_by_date_and_page(
            db, request.start, request.end, request.page, request.limit
        )

    return reservation_repository.find_all_by_user_and_date_and_page(
        db, user, request.start, request.end, request.page, request.limit
    )


def find_by_id(
    db: Session, user: User, reservation_id: int, lock: bool = False
) -> Reservation:
    reservation = reservation_repository.find_by_id(db, reservation_id, lock)
    if not reservation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="존재하지 않는 예약입니다.",
        )

    if user.role != Role.ADMIN and reservation.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="조회할 수 없는 예약 정보입니다.",
        )

    return reservation


def find_available_schedules(
    db: Session, request: GetAvailableScheduleRequest
) -> List[GetAvailableScheduleResponse]:
    reservations = reservation_repository.find_all_by_range_and_status(
        db, request.start, request.end, [ReservationStatus.CONFIRMED], False
    )

    schedules = _generate_slots_with_reservation(
        start=request.start,
        end=request.end,
        reservations=reservations,
    )
    return _merge_schedules(schedules)


def create_reservation(
    db: Session, user: User, request: CreateReservationRequest
) -> Reservation:
    _validate_reservation_datetime(
        db, request.start, request.end, request.number_of_people
    )

    return reservation_repository.create(db, request.toModel(user))


def confirm_reservation(db: Session, user: User, reservation_id: int) -> Reservation:
    reservation = find_by_id(db, user, reservation_id, True)
    _validate_reservation_status(reservation)

    _validate_reservation_datetime(
        db,
        reservation.start_time,
        reservation.end_time,
        reservation.number_of_people,
        True,
    )
    reservation.status = ReservationStatus.CONFIRMED
    return reservation


def update_reservation(
    db: Session, user: User, reservation_id: int, request: UpdateReservationRequest
) -> Reservation:
    reservation = find_by_id(db, user, reservation_id, True)
    _validate_reservation_status(reservation)

    number_of_people = request.number_of_people or reservation.number_of_people
    start = request.start or reservation.start_time
    end = request.end or reservation.end_time

    _validate_reservation_datetime(db, start, end, number_of_people)

    update_data = request.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(reservation, key, value)

    return reservation


def cancel_reservation(db: Session, user: User, reservation_id: int) -> Reservation:
    reservation = find_by_id(db, user, reservation_id)
    _validate_reservation_status(reservation)

    reservation.status = ReservationStatus.CANCELLED
    return reservation


def _validate_reservation_datetime(
    db: Session,
    start: datetime,
    end: datetime,
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
        start,
        end,
        [ReservationStatus.PENDING, ReservationStatus.CONFIRMED],
        lock,
    )

    # 슬롯별로 누적된 예약 수를 가져온다
    schedules = _generate_slots_with_reservation(start, end, reservations)

    # 슬롯 중 하나라도 5만명 초과되는지 체크
    for schedule in schedules:
        if schedule.available_capacity - number_of_people < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="예약 가능 인원을 초과했습니다.",
            )


def _generate_slots_with_reservation(
    start: datetime,
    end: datetime,
    reservations: List[Reservation],
) -> List[int]:
    """
    예약 가능 시간을 반환하는 함수
    예약 가능 시간 조회는 10분단위 조회가 가능하며,
    시작/종료 일자 범위를 10분 단위로 나누고, 각 예약이 차지하는 스케줄을 갱신한다.
    """
    # 1. 스케줄 객체로 초기화
    total_minutes = int((end - start).total_seconds() // 60) // SLOT_MINUTES
    schedules = []
    for idx in range(total_minutes):
        slot_start = start + datetime.timedelta(minutes=idx * SLOT_MINUTES)
        slot_end = slot_start + datetime.timedelta(minutes=SLOT_MINUTES)
        schedules.append(
            GetAvailableScheduleResponse(
                start=slot_start,
                end=slot_end,
                available_capacity=MAX_CAPACITY,
            )
        )

    # 2. 예약을 스케줄에 반영
    for res in reservations:
        if res.status != ReservationStatus.CONFIRMED:
            continue

        start_diff = (res.start_time - start).total_seconds() // 60
        end_diff = (res.end_time - start).total_seconds() // 60

        start_idx = int(start_diff // SLOT_MINUTES)
        end_idx = min(len(schedules), int((end_diff + SLOT_MINUTES) // SLOT_MINUTES))

        for idx in range(start_idx, end_idx):
            schedules[idx].available_capacity -= res.number_of_people

    return schedules


def _merge_schedules(
    schedules: List[GetAvailableScheduleResponse],
) -> List[GetAvailableScheduleResponse]:
    """
    예약이 불가한 스케줄을 필터링하고, 예약 가능 인원이 동일한 연속 구간을 병합하는 함수
    """
    if len(schedules) == 0:
        return []

    schedules = [schedule for schedule in schedules if schedule.available_capacity > 0]

    merged = []
    current = schedules[0]
    for next_schedule in schedules[1:]:
        if (
            current.end == next_schedule.start
            and current.available_capacity == next_schedule.available_capacity
        ):
            current.end = next_schedule.end
            continue

        merged.append(current)
        current = next_schedule
    merged.append(current)

    return merged


def _validate_reservation_status(reservation: Reservation) -> None:
    if reservation.status != ReservationStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="예약 상태를 확인해주세요. 이미 처리된 요청이거나 확정 상태의 예약입니다.",
        )
