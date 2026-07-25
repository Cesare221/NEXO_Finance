from datetime import datetime
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


class MfaStatusResponse(BaseModel):
    enabled: bool
    activated_at: datetime | None = None


class MfaStepUpRequest(BaseModel):
    password: str = Field(min_length=1, max_length=128)


class MfaEnrollResponse(BaseModel):
    secret: str
    otpauth_uri: str


class MfaConfirmRequest(BaseModel):
    code: str = Field(min_length=6, max_length=64)


class MfaConfirmResponse(BaseModel):
    recovery_codes: list[str]


class MfaChallengeRequest(BaseModel):
    challenge_token: str = Field(min_length=32, max_length=256)
    code: str = Field(min_length=6, max_length=64)


class MfaDisableRequest(BaseModel):
    password: str = Field(min_length=1, max_length=128)
    code: str = Field(min_length=6, max_length=64)
