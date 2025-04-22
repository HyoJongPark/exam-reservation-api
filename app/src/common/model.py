from sqlalchemy import Column, DateTime
from sqlalchemy.sql import func

from app.src.config.database import Base


class BaseTable(Base):
    __abstract__ = True  # 테이블 생성 대상이 아님

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    deleted_at = Column(DateTime(timezone=True), nullable=True)
