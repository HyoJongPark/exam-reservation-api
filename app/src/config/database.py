from fastapi import Request
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# PostgreSQL 데이터베이스 URL 설정
SQLALCHEMY_DATABASE_URI = "postgresql://postgres:postgres@db:5432/reservation"

engine = create_engine(SQLALCHEMY_DATABASE_URI, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# 데이터베이스 의존성
def get_db_from_request(request: Request) -> Session:
    db = getattr(request.state, "db", None)
    if db is None:
        raise RuntimeError("DB 세션이 존재하지 않습니다.")
    return db
