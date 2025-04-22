from datetime import datetime

from pydantic import BaseModel

from app.src.user.model import User


class UserCreateResponse(BaseModel):
    id: int
    email: str
    user_name: str
    created_at: datetime

    @staticmethod
    def from_model(user: User) -> "UserCreateResponse":
        return UserCreateResponse(
            id=user.id,
            email=user.email,
            user_name=user.user_name,
            created_at=user.created_at,
        )
