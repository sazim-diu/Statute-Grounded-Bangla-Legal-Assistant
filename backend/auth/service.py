"""Database operations for users (all queries are parameterised)."""
import sqlite3
import time

from backend.auth.security import DUMMY_HASH, hash_password, verify_password
from backend.db.database import get_connection

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_SECONDS = 300

# username -> (failed_count, first_failure_time). In-memory is enough for this project.
_failed: dict[str, tuple[int, float]] = {}


class UserExistsError(Exception):
    pass


class TooManyAttemptsError(Exception):
    pass


def create_user(username: str, password: str, role: str = "user") -> dict:
    password_hash = hash_password(password)
    try:
        with get_connection() as conn:
            cur = conn.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                (username, password_hash, role),
            )
            user_id = cur.lastrowid
    except sqlite3.IntegrityError as exc:
        raise UserExistsError(username) from exc
    return get_user_by_id(user_id)


def get_user_by_id(user_id: int) -> dict | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT user_id, username, role, created_at FROM users WHERE user_id = ?",
            (user_id,),
        ).fetchone()
    return dict(row) if row else None


def list_users() -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT user_id, username, role, created_at FROM users ORDER BY user_id"
        ).fetchall()
    return [dict(r) for r in rows]


def _check_lockout(username: str) -> None:
    entry = _failed.get(username)
    if not entry:
        return
    count, first = entry
    if time.time() - first > LOCKOUT_SECONDS:
        _failed.pop(username, None)
    elif count >= MAX_FAILED_ATTEMPTS:
        raise TooManyAttemptsError(username)


def _record_failure(username: str) -> None:
    count, first = _failed.get(username, (0, time.time()))
    _failed[username] = (count + 1, first)


def authenticate(username: str, password: str) -> dict | None:
    """Return the user dict if credentials are right, otherwise None."""
    _check_lockout(username)
    with get_connection() as conn:
        row = conn.execute(
            "SELECT user_id, username, password_hash, role, created_at "
            "FROM users WHERE username = ?",
            (username,),
        ).fetchone()
    if row is None:
        verify_password(password, DUMMY_HASH)  # keep timing similar
        _record_failure(username)
        return None
    if not verify_password(password, row["password_hash"]):
        _record_failure(username)
        return None
    _failed.pop(username, None)
    return {k: row[k] for k in ("user_id", "username", "role", "created_at")}


def reset_lockouts() -> None:
    _failed.clear()
