import os
import tempfile

# Must be set before the app is imported.
_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_tmp.close()
os.environ["DATABASE_PATH"] = _tmp.name
os.environ["SECRET_KEY"] = "test-secret-key-that-is-at-least-32-characters-long"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from backend.auth import service  # noqa: E402
from backend.db.database import get_connection, init_db  # noqa: E402
from backend.main import app  # noqa: E402


@pytest.fixture()
def client():
    init_db()
    with get_connection() as conn:
        conn.execute("DELETE FROM users")
    service.reset_lockouts()
    with TestClient(app) as c:
        yield c
