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
