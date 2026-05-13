from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=128)
    password: str = Field(min_length=1, max_length=128)


class RegisterRequest(BaseModel):
    username: str = Field(min_length=1, max_length=128)
    password: str = Field(min_length=6, max_length=128)


class UserRead(BaseModel):
    username: str
    created_at: datetime
    avatar_url: str | None = None
    signature: str | None = None

    model_config = {"from_attributes": True}


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead


class RegisterResponse(BaseModel):
    user: UserRead


class ProfileUpdateRequest(BaseModel):
    signature: str | None = Field(default=None, max_length=255)
