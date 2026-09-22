from tests.helpers import create_game, create_table, register_and_login


def test_create_table_invites_guest(client):
    host, host_headers = register_and_login(client, "host@example.com", "host1")
    guest, _ = register_and_login(client, "guest@example.com", "guest1")

    response = create_table(client, host_headers, guest_id=guest["id"])

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "proposing"
    roles = {p["player_id"]: p for p in body["participants"]}
    assert roles[host["id"]]["role"] == "host"
    assert roles[host["id"]]["membership_status"] == "confirmed"
    assert roles[guest["id"]]["role"] == "guest"
    assert roles[guest["id"]]["membership_status"] == "invited"


def test_guest_sees_table_in_their_list(client):
    host, host_headers = register_and_login(client, "host@example.com", "host1")
    guest, guest_headers = register_and_login(client, "guest@example.com", "guest1")
    table = create_table(client, host_headers, guest_id=guest["id"]).json()

    response = client.get("/tables", headers=guest_headers)

    assert response.status_code == 200
    assert [t["id"] for t in response.json()] == [table["id"]]


def test_non_participant_cannot_see_table(client):
    host, host_headers = register_and_login(client, "host@example.com", "host1")
    outsider, outsider_headers = register_and_login(client, "outsider@example.com", "outsider1")
    table = create_table(client, host_headers).json()

    response = client.get(f"/tables/{table['id']}", headers=outsider_headers)

    assert response.status_code == 403


def test_guest_confirms_invite(client):
    host, host_headers = register_and_login(client, "host@example.com", "host1")
    guest, guest_headers = register_and_login(client, "guest@example.com", "guest1")
    table = create_table(client, host_headers, guest_id=guest["id"]).json()

    response = client.post(
        f"/tables/{table['id']}/respond", json={"confirm": True}, headers=guest_headers
    )

    assert response.status_code == 200
    guest_row = next(p for p in response.json()["participants"] if p["player_id"] == guest["id"])
    assert guest_row["membership_status"] == "confirmed"


def test_guest_declines_invite_removes_participant(client):
    host, host_headers = register_and_login(client, "host@example.com", "host1")
    guest, guest_headers = register_and_login(client, "guest@example.com", "guest1")
    table = create_table(client, host_headers, guest_id=guest["id"]).json()

    response = client.post(
        f"/tables/{table['id']}/respond", json={"confirm": False}, headers=guest_headers
    )

    assert response.status_code == 200
    assert all(p["player_id"] != guest["id"] for p in response.json()["participants"])


def test_cannot_propose_before_confirming(client):
    host, host_headers = register_and_login(client, "host@example.com", "host1")
    guest, guest_headers = register_and_login(client, "guest@example.com", "guest1")
    game = create_game(client, host_headers)
    table = create_table(client, host_headers, guest_id=guest["id"]).json()

    response = client.post(
        f"/tables/{table['id']}/propose", json={"game_ids": [game["id"]]}, headers=guest_headers
    )

    assert response.status_code == 400


def test_full_flow_propose_vote_resolve(client):
    host, host_headers = register_and_login(client, "host@example.com", "host1")
    guest, guest_headers = register_and_login(client, "guest@example.com", "guest1")
    azul = create_game(client, host_headers, "Azul")
    table = create_table(client, host_headers, guest_id=guest["id"]).json()
    table_id = table["id"]

    client.post(f"/tables/{table_id}/respond", json={"confirm": True}, headers=guest_headers)

    propose_host = client.post(
        f"/tables/{table_id}/propose", json={"game_ids": [azul["id"]]}, headers=host_headers
    )
    assert propose_host.status_code == 200

    start_voting = client.post(f"/tables/{table_id}/start-voting", headers=host_headers)
    assert start_voting.status_code == 200
    assert start_voting.json()["status"] == "voting"

    vote_host = client.post(
        f"/tables/{table_id}/vote", json={"game_ids": [azul["id"]]}, headers=host_headers
    )
    vote_guest = client.post(
        f"/tables/{table_id}/vote", json={"game_ids": [azul["id"]]}, headers=guest_headers
    )
    assert vote_host.status_code == 200
    assert vote_guest.status_code == 200

    resolve = client.post(
        f"/tables/{table_id}/resolve",
        json={"result_game_ids": [azul["id"]], "result_was_tie": False},
        headers=host_headers,
    )

    assert resolve.status_code == 200
    body = resolve.json()
    assert body["status"] == "resolved"
    assert body["result_game_ids"] == [azul["id"]]


def test_only_host_can_start_voting(client):
    host, host_headers = register_and_login(client, "host@example.com", "host1")
    guest, guest_headers = register_and_login(client, "guest@example.com", "guest1")
    table = create_table(client, host_headers, guest_id=guest["id"]).json()
    client.post(f"/tables/{table['id']}/respond", json={"confirm": True}, headers=guest_headers)

    response = client.post(f"/tables/{table['id']}/start-voting", headers=guest_headers)

    assert response.status_code == 403


def test_vote_respects_planned_games_count(client):
    host, host_headers = register_and_login(client, "host@example.com", "host1")
    azul = create_game(client, host_headers, "Azul")
    tm = create_game(client, host_headers, "Terraforming Mars")
    table = create_table(client, host_headers, planned_games_count=1).json()
    client.post(f"/tables/{table['id']}/start-voting", headers=host_headers)

    response = client.post(
        f"/tables/{table['id']}/vote",
        json={"game_ids": [azul["id"], tm["id"]]},
        headers=host_headers,
    )

    assert response.status_code == 400


def test_host_can_cancel_table(client):
    host, host_headers = register_and_login(client, "host@example.com", "host1")
    table = create_table(client, host_headers).json()

    response = client.post(f"/tables/{table['id']}/cancel", headers=host_headers)

    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"


def test_cannot_cancel_resolved_table(client):
    host, host_headers = register_and_login(client, "host@example.com", "host1")
    azul = create_game(client, host_headers, "Azul")
    table = create_table(client, host_headers).json()
    client.post(f"/tables/{table['id']}/start-voting", headers=host_headers)
    client.post(
        f"/tables/{table['id']}/resolve",
        json={"result_game_ids": [azul["id"]]},
        headers=host_headers,
    )

    response = client.post(f"/tables/{table['id']}/cancel", headers=host_headers)

    assert response.status_code == 400
