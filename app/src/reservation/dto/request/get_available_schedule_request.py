from datetime import datetime, timedelta

from pydantic import BaseModel, Field, field_validator, model_validator

from app.src.reservation.utils.constants import DATE_FORMAT


class GetAvailableScheduleRequest(BaseModel):
    start: datetime = Field(
        ..., description="조회 시작 일자(YYYY-MM-DD)", example="2025-05-01"
    )
    end: datetime = Field(
        ..., description="조회 종료 일자(YYYY-MM-DD)", example="2025-05-01"
    )

    @field_validator("start", "end", mode="before")
    @classmethod
    def validate_datetime_format(cls, value: str) -> str:
        try:
            datetime.strptime(value, DATE_FORMAT)
        except ValueError as e:
            raise ValueError(f"'{value}'은 '{DATE_FORMAT}' 포맷이어야 합니다.") from e
        return value

    @model_validator(mode="after")
    def validate_date_range(self):
        now = datetime.combine(datetime.today(), datetime.min.time())
        min_date = now + timedelta(days=3)
        max_date = now + timedelta(days=180)

        # 1. 3일 이후만 예약 조회만이 가능
        if self.start < min_date:
            raise ValueError("최소 3일 이후 예약 조회만이 가능합니다.")

        # 2. 6개월 이내만 예약 조회만이 가능
        if self.end > max_date:
            raise ValueError(
                "예약 조회는 현재 시점으로부터 180일 이내까지만 가능합니다."
            )

        if self.start > self.end:
            raise ValueError("종료 일자는 시작 일자보다 같거나 커야 합니다.")

        self.end = self.end + timedelta(days=1)
        return self
