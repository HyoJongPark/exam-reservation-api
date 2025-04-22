import datetime
from typing import List
from sqlalchemy.orm import Session

from app.src.reservation.model import Reservation


def create(db: Session, reservation: Reservation) -> Reservation:
    db.add(reservation)
    db.flush()
    db.refresh(reservation)

    return reservation


def find_reservation_by_range(
    db: Session, start_time: datetime, end_time: datetime
) -> List[Reservation]:
    return (
        db.query(Reservation)
        .filter(
            # Reservation.status == ReservationStatus.CONFIRMED,
            Reservation.start_time.between(start_time, end_time),
            Reservation.end_time.between(start_time, end_time),
        )
        .all()
    )
