from tests.helpers import create_game, create_table, register_and_login


def resolve_table(client, host_headers, guest_headers, game_id, table_id):
    client.post(f"/tables/{table_id}/respond", json={"confirm": True}, headers=guest_headers)
    client.post(f"/tables/{table_id}/start-voting", headers=host_headers)
    response = client.post(
        f"/tables/{table_id}/resolve",
        json={"result_game_ids": [game_id]},
        headers=host_headers,
    )
    assert response.status_code == 200, response.text


def test_log_match_for_resolved_table(client):
    host, host_headers = register_and_login(client, "host@example.com", "host1")
    guest, guest_headers = register_and_login(client, "guest@example.com", "guest1")
    azul = create_game(client, host_headers)
    table = create_table(client, host_headers, guest_id=guest["id"]).json()
    resolve_table(client, host_headers, guest_headers, azul["id"], table["id"])

    response = client.post(
        "/matches",
        json={
            "table_id": table["id"],
            "game_id": azul["id"],
            "participant_ids": [host["id"], guest["id"]],
            "date": "2026-10-01",
            "duration": "45 min",
            "winner_id": host["id"],
        },
        headers=host_headers,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["table_id"] == table["id"]
    assert body["winner_id"] == host["id"]

    table_after = client.get(f"/tables/{table['id']}", headers=host_headers).json()
    assert table_after["logged_match_id"] == body["id"]


def test_cannot_log_match_twice_for_same_table(client):
    host, host_headers = register_and_login(client, "host@example.com", "host1")
    guest, guest_headers = register_and_login(client, "guest@example.com", "guest1")
    azul = create_game(client, host_headers)
    table = create_table(client, host_headers, guest_id=guest["id"]).json()
    resolve_table(client, host_headers, guest_headers, azul["id"], table["id"])

    match_payload = {
        "table_id": table["id"],
        "game_id": azul["id"],
        "participant_ids": [host["id"], guest["id"]],
        "date": "2026-10-01",
        "winner_id": host["id"],
    }
    first = client.post("/matches", json=match_payload, headers=host_headers)
    assert first.status_code == 201

    second = client.post("/matches", json=match_payload, headers=host_headers)

    assert second.status_code == 400


def test_cannot_log_match_for_unresolved_table(client):
    host, host_headers = register_and_login(client, "host@example.com", "host1")
    azul = create_game(client, host_headers)
    table = create_table(client, host_headers).json()

    response = client.post(
        "/matches",
        json={
            "table_id": table["id"],
            "game_id": azul["id"],
            "participant_ids": [host["id"]],
            "date": "2026-10-01",
            "winner_id": host["id"],
        },
        headers=host_headers,
    )

    assert response.status_code == 400


def test_standalone_match_with_tie(client):
    host, host_headers = register_and_login(client, "host@example.com", "host1")
    guest, _ = register_and_login(client, "guest@example.com", "guest1")
    azul = create_game(client, host_headers)

    response = client.post(
        "/matches",
        json={
            "game_id": azul["id"],
            "participant_ids": [host["id"], guest["id"]],
            "date": "2026-09-20",
            "is_tie": True,
            "tied_ids": [host["id"], guest["id"]],
        },
        headers=host_headers,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["is_tie"] is True
    assert set(body["tied_ids"]) == {host["id"], guest["id"]}
    assert body["table_id"] is None


def test_cannot_log_match_you_did_not_play(client):
    host, host_headers = register_and_login(client, "host@example.com", "host1")
    guest, _ = register_and_login(client, "guest@example.com", "guest1")
    azul = create_game(client, host_headers)

    response = client.post(
        "/matches",
        json={
            "game_id": azul["id"],
            "participant_ids": [guest["id"]],
            "date": "2026-09-20",
            "winner_id": guest["id"],
        },
        headers=host_headers,
    )

    assert response.status_code == 400


def test_rejects_ambiguous_outcome(client):
    host, host_headers = register_and_login(client, "host@example.com", "host1")
    azul = create_game(client, host_headers)

    response = client.post(
        "/matches",
        json={
            "game_id": azul["id"],
            "participant_ids": [host["id"]],
            "date": "2026-09-20",
            "winner_id": host["id"],
            "is_tie": True,
            "tied_ids": [host["id"]],
        },
        headers=host_headers,
    )

    assert response.status_code == 400


def test_list_matches_only_returns_mine(client):
    host, host_headers = register_and_login(client, "host@example.com", "host1")
    outsider, outsider_headers = register_and_login(client, "outsider@example.com", "outsider1")
    azul = create_game(client, host_headers)
    client.post(
        "/matches",
        json={
            "game_id": azul["id"],
            "participant_ids": [host["id"]],
            "date": "2026-09-20",
            "winner_id": host["id"],
        },
        headers=host_headers,
    )

    response = client.get("/matches", headers=outsider_headers)

    assert response.status_code == 200
    assert response.json() == []


def test_get_match_forbidden_for_non_participant(client):
    host, host_headers = register_and_login(client, "host@example.com", "host1")
    outsider, outsider_headers = register_and_login(client, "outsider@example.com", "outsider1")
    azul = create_game(client, host_headers)
    match = client.post(
        "/matches",
        json={
            "game_id": azul["id"],
            "participant_ids": [host["id"]],
            "date": "2026-09-20",
            "winner_id": host["id"],
        },
        headers=host_headers,
    ).json()

    response = client.get(f"/matches/{match['id']}", headers=outsider_headers)

    assert response.status_code == 403
