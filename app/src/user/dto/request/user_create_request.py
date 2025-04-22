from pydantic import BaseModel

from app.src.user.model import Role, User


class UserCreateRequest(BaseModel):
    email: str
    password: str
    user_name: str
    role: Role = Role.USER

    def toModel(self) -> User:
        return User(
            email=self.email,
            password=self.password,
            user_name=self.user_name,
            role=self.role,
        )
