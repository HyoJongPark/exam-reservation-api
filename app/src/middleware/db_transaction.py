from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.src.config.database import SessionLocal


class DBSessionMiddleware(BaseHTTPMiddleware):
    """
    DB 세션을 관리하는 미들웨어
    요청 전체를 래핑하여 DB 세션을 관리합니다.

    요청이 들어오면 세션을 생성하고, 종료 시점에 commit or rollback을 통해 하나의 요청이 하나의 트랜잭션으로 관리되도록합니다.
    """

    async def dispatch(self, request: Request, call_next):
        db = SessionLocal()
        request.state.db = db  # 세션을 request.state에 저장

        try:
            response = await call_next(request)
            db.commit()  # 요청 처리 성공하면 커밋
            return response
        except Exception as e:
            db.rollback()  # 실패하면 롤백
            raise e
        finally:
            db.close()  # 무조건 세션 닫아줌
