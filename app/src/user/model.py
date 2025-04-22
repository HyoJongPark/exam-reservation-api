from enum import Enum
import enum
from sqlalchemy import Column, ForeignKey, Integer, String

from app.src.common.model import BaseTable


class Role(str, enum.Enum):
    ADMIN = "admin"
    USER = "user"


class User(BaseTable):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    user_name = Column(String)
    role = Column(Enum(Role), default=Role.USER)
    company_id = Column(Integer, ForeignKey("companies.id"))
