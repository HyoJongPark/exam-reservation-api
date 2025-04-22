from datetime import datetime
from pydantic import BaseModel

from app.src.reservation.model import Reservation, ReservationStatus


class ReservationResponse(BaseModel):
    id: int
    start_time: datetime
    end_time: datetime
    number_of_people: int
    status: ReservationStatus
    created_at: datetime

    @classmethod
    def from_model(cls, reservation: Reservation) -> "ReservationResponse":
        return cls(
            id=reservation.id,
            start_time=reservation.start_time,
            end_time=reservation.end_time,
            number_of_people=reservation.number_of_people,
            status=reservation.status,
            created_at=reservation.created_at,
        )
