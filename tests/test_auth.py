def register(client, **overrides):
    payload = {
        "email": "gonza@example.com",
        "username": "gonza",
        "name": "Gonza",
        "password": "supersecreto",
        **overrides,
    }
    return client.post("/auth/register", json=payload)


def test_register_creates_user(client):
    response = register(client)

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "gonza@example.com"
    assert body["username"] == "gonza"
    assert "password" not in body
    assert "hashed_password" not in body


def test_register_rejects_duplicate_email(client):
    register(client)

    response = register(client, username="otro")

    assert response.status_code == 400


def test_register_rejects_duplicate_username(client):
    register(client)

    response = register(client, email="otro@example.com")

    assert response.status_code == 400


def test_login_returns_token(client):
    register(client)

    response = client.post(
        "/auth/login", json={"email": "gonza@example.com", "password": "supersecreto"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_login_rejects_wrong_password(client):
    register(client)

    response = client.post(
        "/auth/login", json={"email": "gonza@example.com", "password": "incorrecta"}
    )

    assert response.status_code == 401


def test_login_rejects_unknown_email(client):
    response = client.post(
        "/auth/login", json={"email": "nadie@example.com", "password": "supersecreto"}
    )

    assert response.status_code == 401


def test_me_returns_current_user_with_valid_token(client):
    register(client)
    login = client.post(
        "/auth/login", json={"email": "gonza@example.com", "password": "supersecreto"}
    )
    token = login.json()["access_token"]

    response = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["email"] == "gonza@example.com"


def test_me_rejects_missing_token(client):
    response = client.get("/users/me")

    assert response.status_code == 401


def test_me_rejects_invalid_token(client):
    response = client.get("/users/me", headers={"Authorization": "Bearer not-a-real-token"})

    assert response.status_code == 401
