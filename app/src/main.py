from fastapi import FastAPI

from app.src.config.database import Base, engine
from app.src.middleware.db_transaction import DBSessionMiddleware
from app.src.user.router import router as user_router
from app.src.reservation.router import router as reservation_router

# initialize fastapi
app = FastAPI()
app.include_router(user_router)
app.include_router(reservation_router)

app.add_middleware(DBSessionMiddleware)

# initialize database
Base.metadata.create_all(engine)


@app.get("/")
async def warmup():
    ## 초기 데이터 생성
    return {"message": "Hello World"}
