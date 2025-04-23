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

            # TODO: 상태 코드를 사용해서 rollback 처리하는건 좋지 않아보임.
            # 예외처리 핸들러에서 가로채지는 예외를 어떻게 미들웨어에서 사용할 수 있는지 고민해봐야함.
            if response.status_code >= 400:
                db.rollback()
            else:
                db.commit()
            return response
        finally:
            db.close()  # 무조건 세션 닫아줌
