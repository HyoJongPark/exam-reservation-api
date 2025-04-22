from datetime import datetime

from pydantic import BaseModel, Field, field_validator, model_validator

from app.src.reservation.utils.constants import DATETIME_FORMAT, MAX_CAPACITY


class UpdateReservationRequest(BaseModel):
    start_time: datetime | None = None
    end_time: datetime | None = None
    number_of_people: int | None = Field(default=None, ge=1, le=MAX_CAPACITY)

    @classmethod
    @field_validator("start_time", "end_time", mode="before")
    def validate_datetime_format(cls, value: str) -> str:
        try:
            datetime.strptime(value, DATETIME_FORMAT)
        except ValueError as e:
            raise ValueError(
                f"예약 일정 형식은 '{DATETIME_FORMAT}' 포맷이어야 합니다."
            ) from e
        return value

    @model_validator(mode="after")
    def validate_data_exist(self):
        if not self.start_time and not self.number_of_people:
            raise ValueError("수정 데이터가 존재하지 않습니다.")
        return self
