from datetime import datetime

from pydantic import BaseModel, Field, field_validator, model_validator

from app.src.reservation.utils.constants import DATE_FORMAT


class GetReservationsRequest(BaseModel):
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=10, ge=10)
    start_date: datetime
    end_date: datetime

    @field_validator("start_date", "end_date", mode="before")
    @classmethod
    def validate_datetime_format(cls, value: str) -> str:
        try:
            datetime.strptime(value, DATE_FORMAT)
        except ValueError as e:
            raise ValueError(
                f"예약 일정 형식은 '{DATE_FORMAT}' 포맷이어야 합니다."
            ) from e
        return value

    @model_validator(mode="after")
    def validate_datetime(self):
        if self.start_date > self.end_date:
            raise ValueError("종료 일자는 시작 일자보다 같거나 커야 합니다.")

        self.end_date = datetime.combine(self.end_date, datetime.max.time())

        return self
