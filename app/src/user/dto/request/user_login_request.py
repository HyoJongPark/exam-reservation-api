from pydantic import BaseModel, Field


class UserLoginRequest(BaseModel):
    email: str = Field(..., description="이메일", example="test@test.com")
    password: str = Field(..., description="비밀번호", example="password")
