from typing import Literal
from pydantic import BaseModel, EmailStr, Field


class EmailRequest(BaseModel):
    email: EmailStr


class TokenConfirmation(BaseModel):
    token: str = Field(min_length=32, max_length=256)


class PasswordResetConfirmation(TokenConfirmation):
    new_password: str = Field(min_length=12, max_length=128)


class RegistrationResponse(BaseModel):
    status: Literal["verification_required"] = "verification_required"
    email: EmailStr
