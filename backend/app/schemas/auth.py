from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field

from app.schemas.user import ProfileOut


class SignupIn(BaseModel):
    email: EmailStr
    name: str = Field(min_length=1, max_length=160)
    password: str = Field(min_length=1, max_length=200)


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=200)


class ChangePasswordIn(BaseModel):
    current_password: str = Field(min_length=1, max_length=200)
    new_password: str = Field(min_length=1, max_length=200)


class SessionOut(BaseModel):
    """Returned on sign-up and sign-in.

    The token is handed to the Next.js server, which stores it in an httpOnly
    cookie. It is never exposed to browser JavaScript.
    """

    token: str
    expires_at: str
    user: ProfileOut
