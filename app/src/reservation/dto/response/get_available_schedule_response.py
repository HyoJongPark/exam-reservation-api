from datetime import datetime
from pydantic import BaseModel


class GetAvailableScheduleResponse(BaseModel):
    start: datetime
    end: datetime
    available_capacity: int
