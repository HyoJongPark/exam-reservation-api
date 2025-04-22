from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.src.config.database import SessionLocal


class DBSessionMiddleware(BaseHTTPMiddleware):
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
