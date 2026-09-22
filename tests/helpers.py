def register_and_login(client, email: str, username: str, password: str = "supersecreto"):
    register = client.post(
        "/auth/register",
        json={"email": email, "username": username, "name": username.title(), "password": password},
    )
    assert register.status_code == 201, register.text
    user = register.json()

    login = client.post("/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200, login.text
    token = login.json()["access_token"]

    return user, {"Authorization": f"Bearer {token}"}


def create_game(client, headers, name="Azul"):
    response = client.post("/games", json={"name": name}, headers=headers)
    assert response.status_code == 201, response.text
    return response.json()


def create_table(client, headers, guest_id=None, **overrides):
    payload = {
        "date": "2026-10-01",
        "time": "20:00",
        "planned_games_count": 1,
        "participant_ids": [guest_id] if guest_id else [],
        **overrides,
    }
    return client.post("/tables", json=payload, headers=headers)
