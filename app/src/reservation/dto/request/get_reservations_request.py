from datetime import datetime

from pydantic import BaseModel, Field, field_validator, model_validator

from app.src.reservation.utils.constants import DATE_FORMAT
from app.src.reservation.utils.model_validator import validate_reservation_date_format


class GetReservationsRequest(BaseModel):
    page: int = Field(default=1, ge=1, description="페이지 번호", example=1)
    limit: int = Field(default=10, ge=10, description="페이지 당 조회 개수", example=10)
    start: datetime = Field(
        ..., description="조회 시작 일자(YYYY-MM-DD)", example="2025-05-01"
    )
    end: datetime = Field(
        ..., description="조회 종료 일자(YYYY-MM-DD)", example="2025-05-01"
    )

    @field_validator("start", "end", mode="before")
    @classmethod
    def validate_datetime_format(cls, value: str) -> str:
        validate_reservation_date_format(value, DATE_FORMAT)
        return value

    @model_validator(mode="after")
    def validate_datetime(self):
        if self.start > self.end:
            raise ValueError("종료 일자는 시작 일자보다 같거나 커야 합니다.")

        self.end = datetime.combine(self.end, datetime.max.time())

        return self
