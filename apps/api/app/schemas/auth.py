import base64
import binascii
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator

ThemePreference = Literal["system", "light", "dark"]


class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=12, max_length=128)
    privacy_accepted: bool = False
    ai_data_processing_consent: bool = False


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class DeleteAccountRequest(BaseModel):
    password: str = Field(..., min_length=1, max_length=128)


class UserSessionResponse(BaseModel):
    id: int
    device_name: str | None
    created_at: datetime
    last_used_at: datetime
    expires_at: datetime

    model_config = {"from_attributes": True}


class MeResponse(BaseModel):
    id: int
    name: str
    email: str
    phone: str | None
    avatar_data_url: str | None
    theme_preference: ThemePreference
    privacy_policy_version: str | None
    privacy_accepted_at: str | None
    ai_data_processing_consent: bool


class ProfileUpdateRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    phone: str | None = Field(None, min_length=8, max_length=32, pattern=r"^[0-9+() .-]+$")
    avatar_data_url: str | None = Field(None, max_length=350_000)
    theme_preference: ThemePreference | None = None
    ai_data_processing_consent: bool | None = None

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        clean = value.strip()
        if not clean:
            raise ValueError("Name cannot be empty")
        return clean

    @field_validator("phone")
    @classmethod
    def normalize_phone(cls, value: str | None) -> str | None:
        return value.strip() if value else None

    @field_validator("avatar_data_url")
    @classmethod
    def validate_avatar(cls, value: str | None) -> str | None:
        if value is None:
            return None
        prefixes = {
            "data:image/png;base64,": b"\x89PNG\r\n\x1a\n",
            "data:image/jpeg;base64,": b"\xff\xd8\xff",
            "data:image/webp;base64,": b"RIFF",
        }
        prefix = next((item for item in prefixes if value.startswith(item)), None)
        if prefix is None:
            raise ValueError("Avatar must be a PNG, JPEG or WebP data URL")
        try:
            content = base64.b64decode(value[len(prefix):], validate=True)
        except (binascii.Error, ValueError) as error:
            raise ValueError("Avatar contains invalid base64 data") from error
        if len(content) > 256 * 1024:
            raise ValueError("Avatar must not exceed 256 KB")
        if not content.startswith(prefixes[prefix]):
            raise ValueError("Avatar content does not match its media type")
        if prefix.startswith("data:image/webp") and content[8:12] != b"WEBP":
            raise ValueError("Avatar content does not match its media type")
        return value
