import datetime
from typing import List
from sqlalchemy.orm import Session

from app.src.reservation.model import Reservation, ReservationStatus
from app.src.user.model import User


def create(db: Session, reservation: Reservation) -> Reservation:
    db.add(reservation)
    db.flush()
    db.refresh(reservation)

    return reservation


def find_by_id(db: Session, reservation_id: int, lock: bool = False) -> Reservation:
    query = db.query(Reservation).filter(Reservation.id == reservation_id)
    if lock:
        query = query.with_for_update()
    return query.first()


def find_all_by_date_and_page(
    db: Session, start: datetime, end: datetime, page: int, limit: int
) -> List[Reservation]:
    return (
        db.query(Reservation)
        .filter(
            Reservation.start_time.between(start, end),
            Reservation.end_time.between(start, end),
        )
        .order_by(Reservation.start_time.asc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )


def find_all_by_user_and_date_and_page(
    db: Session,
    user: User,
    start: datetime,
    end: datetime,
    page: int,
    limit: int,
) -> List[Reservation]:
    return (
        db.query(Reservation)
        .filter(
            Reservation.user_id == user.id,
            Reservation.start_time.between(start, end),
            Reservation.end_time.between(start, end),
        )
        .order_by(Reservation.start_time.asc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )


def find_all_by_range_and_status(
    db: Session,
    start: datetime,
    end: datetime,
    status: List[ReservationStatus],
    lock: bool,
) -> List[Reservation]:
    query = db.query(Reservation).filter(
        Reservation.start_time.between(start, end),
        Reservation.end_time.between(start, end),
        Reservation.status.in_(status),
    )

    if lock:
        query = query.with_for_update()

    return query.all()
