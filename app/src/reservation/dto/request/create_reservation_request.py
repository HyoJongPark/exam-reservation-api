from datetime import datetime

from pydantic import BaseModel, Field, field_validator, model_validator

from app.src.reservation.model import Reservation
from app.src.reservation.utils.constants import DATETIME_FORMAT, MAX_CAPACITY
from app.src.reservation.utils.model_validator import (
    validate_reservation_date_format,
    validate_reservation_datetime,
)
from app.src.user.model import User


class CreateReservationRequest(BaseModel):
    start: datetime = Field(
        ..., description="예약 시작 시간(YYYY-MM-DD HH:MM)", example="2025-05-01 12:00"
    )
    end: datetime = Field(
        ..., description="예약 종료 시간(YYYY-MM-DD HH:MM)", example="2025-05-01 13:00"
    )
    reservation_name: str = Field(..., description="일정 명")
    number_of_people: int = Field(
        default=1, ge=1, le=MAX_CAPACITY, description="예약 인원 수", example=1
    )

    @field_validator("start", "end", mode="before")
    @classmethod
    def validate_datetime_format(cls, value: str) -> str:
        validate_reservation_date_format(value, DATETIME_FORMAT)
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
