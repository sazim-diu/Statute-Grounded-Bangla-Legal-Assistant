from backend.auth import service

GOOD = {"username": "Rahim_01", "password": "Strong#Pass1"}


def register(client, **overrides):
    return client.post("/auth/register", json={**GOOD, **overrides})


def login(client, username="rahim_01", password="Strong#Pass1"):
    return client.post("/auth/login", json={"username": username, "password": password})


def test_register_success_and_username_normalised(client):
    r = register(client)
    assert r.status_code == 201
    body = r.json()
    assert body["username"] == "rahim_01"
    assert body["role"] == "user"
    assert "password" not in body and "password_hash" not in body


def test_password_is_hashed_in_database(client):
    from backend.db.database import get_connection

    register(client)
    with get_connection() as conn:
        stored = conn.execute("SELECT password_hash FROM users").fetchone()[0]
    assert stored != GOOD["password"]
    assert stored.startswith("$2")  # bcrypt


def test_duplicate_username_rejected(client):
    register(client)
    assert register(client).status_code == 409


def test_weak_passwords_rejected(client):
    for pw in ["short1A", "alllowercase1", "ALLUPPERCASE1", "NoDigitsHere", "x" * 80 + "Aa1"]:
        assert register(client, password=pw).status_code == 422, pw


def test_bad_usernames_rejected(client):
    for name in ["ab", "has space", "bad-char!", "x" * 31, "'; DROP TABLE users;--"]:
        assert register(client, username=name).status_code == 422, name


def test_password_cannot_contain_username(client):
    r = register(client, username="rahim_01", password="Rahim_01-Pass9")
    assert r.status_code == 422


def test_login_success_and_me(client):
    register(client)
    r = login(client)
    assert r.status_code == 200
    token = r.json()["access_token"]
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["username"] == "rahim_01"


def test_login_wrong_password_and_unknown_user_same_message(client):
    register(client)
    wrong = login(client, password="Wrong#Pass1")
    unknown = login(client, username="nobody")
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json() == unknown.json()


def test_me_requires_token(client):
    assert client.get("/auth/me").status_code == 401
    bad = client.get("/auth/me", headers={"Authorization": "Bearer not.a.token"})
    assert bad.status_code == 401


def test_admin_route_forbidden_for_normal_user(client):
    register(client)
    token = login(client).json()["access_token"]
    r = client.get("/auth/users", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403


def test_admin_route_allowed_for_admin(client):
    service.create_user("admin_one", "Admin#Pass123", role="admin")
    token = login(client, "admin_one", "Admin#Pass123").json()["access_token"]
    r = client.get("/auth/users", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()[0]["username"] == "admin_one"


def test_lockout_after_repeated_failures(client):
    register(client)
    for _ in range(5):
        assert login(client, password="Wrong#Pass1").status_code == 401
    assert login(client).status_code == 429
