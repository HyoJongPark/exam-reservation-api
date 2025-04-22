from datetime import datetime
from pydantic import BaseModel


class GetAvailableScheduleResponse(BaseModel):
    start_time: datetime
    end_time: datetime
    available_capacity: int
