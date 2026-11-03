"""Request/response models and input validation for authentication."""
import re

from pydantic import BaseModel, field_validator, model_validator

USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{3,30}$")
MAX_PASSWORD_BYTES = 72  # bcrypt ignores everything after 72 bytes


class RegisterRequest(BaseModel):
    username: str
    password: str

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        v = v.strip().lower()
        if not USERNAME_RE.match(v):
            raise ValueError(
                "Username must be 3-30 characters: letters, digits and underscore only"
            )
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if len(v.encode("utf-8")) > MAX_PASSWORD_BYTES:
            raise ValueError("Password is too long (max 72 bytes)")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain a lowercase letter")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain an uppercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain a digit")
        return v

    @model_validator(mode="after")
    def password_not_username(self):
        if self.username and self.username in self.password.lower():
            raise ValueError("Password must not contain the username")
        return self


class LoginRequest(BaseModel):
    username: str
    password: str

    @field_validator("username")
    @classmethod
    def normalise_username(cls, v: str) -> str:
        v = v.strip().lower()
        if not v or len(v) > 30:
            raise ValueError("Invalid username")
        return v

    @field_validator("password")
    @classmethod
    def limit_password(cls, v: str) -> str:
        if not v or len(v) > 128:
            raise ValueError("Invalid password")
        return v


class UserOut(BaseModel):
    user_id: int
    username: str
    role: str
    created_at: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
