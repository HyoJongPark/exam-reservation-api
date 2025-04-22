import enum
from sqlalchemy import Column, ForeignKey, Integer, DateTime, Enum, String
from sqlalchemy.orm import relationship

from app.src.common.model import BaseTable


class ReservationStatus(str, enum.Enum):
    PENDING = "pending"
    REJECTED = "rejected"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"


class Reservation(BaseTable):
    __tablename__ = "reservations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    reservation_name = Column(String, nullable=False)
    number_of_people = Column(Integer, nullable=False)
    status = Column(Enum(ReservationStatus), default=ReservationStatus.PENDING)

    user = relationship("User")
