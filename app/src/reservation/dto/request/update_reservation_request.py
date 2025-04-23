from datetime import datetime

from pydantic import BaseModel, Field, field_validator, model_validator

from app.src.reservation.utils.constants import DATETIME_FORMAT, MAX_CAPACITY
from app.src.reservation.utils.validator import (
    validate_reservation_date_format,
    validate_reservation_datetime,
)


class UpdateReservationRequest(BaseModel):
    start: datetime | None = Field(
        default=None,
        description="예약 시작 시간(YYYY-MM-DD HH:MM)",
        example="2025-05-01 12:00",
    )
    end: datetime | None = Field(
        default=None,
        description="예약 종료 시간(YYYY-MM-DD HH:MM)",
        example="2025-05-01 13:00",
    )
    number_of_people: int | None = Field(
        default=None,
        ge=1,
        le=MAX_CAPACITY,
        description="예약 인원 수",
        example=1,
    )

    @classmethod
    @field_validator("start", "end", mode="before")
    def validate_datetime_format(cls, value: str) -> str:
        validate_reservation_date_format(value, DATETIME_FORMAT)
        return value

    @model_validator(mode="after")
    def validate_data_exist(self):
        if not self.start and not self.number_of_people:
            raise ValueError("수정 데이터가 존재하지 않습니다.")

        if (self.start and not self.end) or (self.end and not self.start):
            raise ValueError("시간 변경 시 시작/종료 시간 모두 입력되어야 합니다.")
        if self.start and self.end:
            validate_reservation_datetime(self.start, self.end)

        return self
