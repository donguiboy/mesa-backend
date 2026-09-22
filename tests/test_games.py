from tests.helpers import register_and_login


def test_create_game_only_needs_a_name(client):
    _, headers = register_and_login(client, "host@example.com", "host1")

    response = client.post("/games", json={"name": "Azul"}, headers=headers)

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Azul"
    assert body["bgg_id"] is None
    assert body["description"] is None


def test_list_games_is_public(client):
    response = client.get("/games")

    assert response.status_code == 200
    assert response.json() == []
