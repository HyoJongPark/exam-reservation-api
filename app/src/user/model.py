from enum import Enum as PyEnum  # Python 표준 Enum
from sqlalchemy import Enum as SqlEnum  # SQLAlchemy용 Enum
from sqlalchemy import Column, Integer, String

from app.src.common.model import BaseTable


class Role(str, PyEnum):
    ADMIN = "admin"
    USER = "user"


class User(BaseTable):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    user_name = Column(String)
    role = Column(SqlEnum(Role), default=Role.USER)
