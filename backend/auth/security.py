"""Password hashing (bcrypt) and JWT helpers. No secrets are hardcoded."""
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from backend import config

ALGORITHM = "HS256"


def get_secret() -> str:
    if not config.SECRET_KEY or len(config.SECRET_KEY) < 32:
        raise RuntimeError(
            "SECRET_KEY is missing or too short. Set a random value of at least 32 "
            "characters in your .env file."
        )
    return config.SECRET_KEY


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


# Used so that a login for an unknown user takes about as long as a real one.
DUMMY_HASH = hash_password("not-a-real-password-just-for-timing")


def create_access_token(user_id: int, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "role": role, "exp": expire}
    return jwt.encode(payload, get_secret(), algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, get_secret(), algorithms=[ALGORITHM])
    except JWTError:
        return None
