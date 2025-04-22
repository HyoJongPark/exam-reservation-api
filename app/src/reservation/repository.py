import datetime
from typing import List
from sqlalchemy.orm import Session

from app.src.reservation.model import Reservation


def create(db: Session, reservation: Reservation) -> Reservation:
    db.add(reservation)
    db.flush()
    db.refresh(reservation)

    return reservation


def find_all_by_range(
    db: Session, start_time: datetime, end_time: datetime, lock: bool
) -> List[Reservation]:
    query = db.query(Reservation).filter(
        Reservation.start_time.between(start_time, end_time),
        Reservation.end_time.between(start_time, end_time),
    )

    if lock:
        query = query.with_for_update()

    return query.all()
