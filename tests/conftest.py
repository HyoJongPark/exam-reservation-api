# tests/conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.src.config.database import Base  # 실제 모델 정의된 Base

# 테스트용 PostgreSQL 연결 URL
# TEST_DATABASE_URL = "postgresql://postgres:postgres@localhost:5433/reservation-test-db"
TEST_DATABASE_URL = "postgresql://postgres:postgres@test-db:5432/reservation-test-db"

engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()
