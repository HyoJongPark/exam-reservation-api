from datetime import datetime

from pydantic import BaseModel, Field, field_validator, model_validator

from app.src.reservation.model import Reservation
from app.src.reservation.utils.constants import DATETIME_FORMAT, MAX_CAPACITY
from app.src.reservation.utils.validator import validate_reservation_datetime
from app.src.user.model import User


class CreateReservationRequest(BaseModel):
    start: datetime
    end: datetime
    reservation_name: str
    number_of_people: int = Field(default=1, ge=1, le=MAX_CAPACITY)

    @field_validator("start", "end", mode="before")
    @classmethod
    def validate_datetime_format(cls, value: str) -> str:
        try:
            datetime.strptime(value, DATETIME_FORMAT)
        except ValueError as e:
            raise ValueError(
                f"예약 일정 형식은 '{DATETIME_FORMAT}' 포맷이어야 합니다."
            ) from e
        return value

    @model_validator(mode="after")
    def validate_reservation_datetime(self):
        validate_reservation_datetime(self.start, self.end)
        return self

    def toModel(self, user: User) -> Reservation:
        return Reservation(
            user_id=user.id,
            start_time=self.start,
            end_time=self.end,
            number_of_people=self.number_of_people,
            reservation_name=self.reservation_name,
        )
