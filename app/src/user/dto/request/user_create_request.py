from pydantic import BaseModel, Field

from app.src.user.model import Role, User


class UserCreateRequest(BaseModel):
    email: str = Field(..., description="이메일", example="test@test.com")
    password: str = Field(..., description="비밀번호", example="password")
    user_name: str = Field(..., description="이름", example="홍길동")
    role: Role = Field(
        default=Role.USER, description="계정 권한(user or admin)", example=Role.ADMIN
    )

    def toModel(self) -> User:
        return User(
            email=self.email,
            password=self.password,
            user_name=self.user_name,
            role=self.role,
        )
