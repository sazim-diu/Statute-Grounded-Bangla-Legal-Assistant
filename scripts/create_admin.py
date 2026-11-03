"""Create an admin user. The password is typed at the prompt, never stored in code.

Usage: python scripts/create_admin.py
"""
import getpass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pydantic import ValidationError  # noqa: E402

from backend.auth import service  # noqa: E402
from backend.auth.schemas import RegisterRequest  # noqa: E402
from backend.db.database import init_db  # noqa: E402


def main() -> None:
    init_db()
    username = input("Admin username: ")
    password = getpass.getpass("Admin password: ")
    try:
        data = RegisterRequest(username=username, password=password)
    except ValidationError as exc:
        sys.exit("Invalid input:\n" + "\n".join(e["msg"] for e in exc.errors()))
    try:
        user = service.create_user(data.username, data.password, role="admin")
    except service.UserExistsError:
        sys.exit("That username already exists.")
    print(f"Admin '{user['username']}' created.")


if __name__ == "__main__":
    main()
