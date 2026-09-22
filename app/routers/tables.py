import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.session import get_db
from app.deps import get_current_user
from app.models.enums import MembershipStatus, ParticipantRole, ProposalStatus, TableStatus
from app.models.game import Game
from app.models.game_table import GameTable
from app.models.table_participant import TableParticipant
from app.models.user import User
from app.schemas.table import (
    InviteParticipants,
    ProposeGames,
    ResolveTable,
    RespondInvite,
    TableCreate,
    TableRead,
    VoteGames,
)

router = APIRouter(prefix="/tables", tags=["tables"])


def _get_table(db: Session, table_id: uuid.UUID) -> GameTable:
    table = db.get(GameTable, table_id, options=[selectinload(GameTable.participants)])
    if table is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Mesa no encontrada")
    return table


def _find_participant(table: GameTable, user_id: uuid.UUID) -> TableParticipant | None:
    return next((p for p in table.participants if p.player_id == user_id), None)


def _require_participant(table: GameTable, user_id: uuid.UUID) -> TableParticipant:
    participant = _find_participant(table, user_id)
    if participant is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "No sos parte de esta mesa")
    return participant


def _require_host(table: GameTable, user_id: uuid.UUID) -> None:
    if table.host_id != user_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Solo el host puede hacer esto")


def _require_existing_users(db: Session, user_ids: list[uuid.UUID]) -> None:
    found = set(db.scalars(select(User.id).where(User.id.in_(user_ids))))
    missing = set(user_ids) - found
    if missing:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Usuario(s) no encontrado(s): {missing}")


def _require_existing_games(db: Session, game_ids: list[uuid.UUID]) -> None:
    found = set(db.scalars(select(Game.id).where(Game.id.in_(game_ids))))
    missing = set(game_ids) - found
    if missing:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Juego(s) no encontrado(s): {missing}")


@router.post("", response_model=TableRead, status_code=status.HTTP_201_CREATED)
def create_table(
    payload: TableCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> GameTable:
    guest_ids = [pid for pid in payload.participant_ids if pid != current_user.id]
    if guest_ids:
        _require_existing_users(db, guest_ids)

    table = GameTable(
        host_id=current_user.id,
        date=payload.date,
        time=payload.time,
        planned_games_count=payload.planned_games_count,
        vibe_genres=payload.vibe_genres,
        description=payload.description,
    )
    table.participants.append(
        TableParticipant(
            player_id=current_user.id,
            role=ParticipantRole.HOST,
            membership_status=MembershipStatus.CONFIRMED,
        )
    )
    for guest_id in guest_ids:
        table.participants.append(
            TableParticipant(player_id=guest_id, role=ParticipantRole.GUEST)
        )

    db.add(table)
    db.commit()
    db.refresh(table)
    return table


@router.get("", response_model=list[TableRead])
def list_my_tables(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[GameTable]:
    table_ids = db.scalars(
        select(TableParticipant.table_id).where(TableParticipant.player_id == current_user.id)
    )
    return list(
        db.scalars(
            select(GameTable)
            .where(GameTable.id.in_(table_ids))
            .options(selectinload(GameTable.participants))
            .order_by(GameTable.date, GameTable.time)
        )
    )


@router.get("/{table_id}", response_model=TableRead)
def get_table(
    table_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> GameTable:
    table = _get_table(db, table_id)
    _require_participant(table, current_user.id)
    return table


@router.post("/{table_id}/invite", response_model=TableRead)
def invite_participants(
    table_id: uuid.UUID,
    payload: InviteParticipants,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> GameTable:
    table = _get_table(db, table_id)
    _require_host(table, current_user.id)

    already_in = {p.player_id for p in table.participants}
    new_ids = [pid for pid in payload.participant_ids if pid not in already_in]
    if new_ids:
        _require_existing_users(db, new_ids)
        for guest_id in new_ids:
            table.participants.append(
                TableParticipant(table_id=table.id, player_id=guest_id, role=ParticipantRole.GUEST)
            )
        db.commit()
        db.refresh(table)
    return table


@router.post("/{table_id}/respond", response_model=TableRead)
def respond_invite(
    table_id: uuid.UUID,
    payload: RespondInvite,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> GameTable:
    table = _get_table(db, table_id)
    participant = _require_participant(table, current_user.id)

    if participant.membership_status != MembershipStatus.INVITED:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Esta invitación ya fue respondida")

    if payload.confirm:
        participant.membership_status = MembershipStatus.CONFIRMED
    else:
        table.participants.remove(participant)

    db.commit()
    db.refresh(table)
    return table


@router.post("/{table_id}/propose", response_model=TableRead)
def propose_games(
    table_id: uuid.UUID,
    payload: ProposeGames,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> GameTable:
    table = _get_table(db, table_id)
    participant = _require_participant(table, current_user.id)

    if table.status != TableStatus.PROPOSING:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "La mesa ya no está recibiendo propuestas")
    if participant.membership_status != MembershipStatus.CONFIRMED:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Confirmá tu asistencia antes de proponer")

    _require_existing_games(db, payload.game_ids)

    participant.proposed_game_ids = payload.game_ids
    participant.proposal_status = ProposalStatus.SENT
    db.commit()
    db.refresh(table)
    return table


@router.post("/{table_id}/start-voting", response_model=TableRead)
def start_voting(
    table_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> GameTable:
    table = _get_table(db, table_id)
    _require_host(table, current_user.id)

    if table.status != TableStatus.PROPOSING:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "La mesa no está en etapa de propuestas")

    table.status = TableStatus.VOTING
    db.commit()
    db.refresh(table)
    return table


@router.post("/{table_id}/vote", response_model=TableRead)
def vote_games(
    table_id: uuid.UUID,
    payload: VoteGames,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> GameTable:
    table = _get_table(db, table_id)
    participant = _require_participant(table, current_user.id)

    if table.status != TableStatus.VOTING:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "La mesa no está en etapa de votación")
    if participant.membership_status != MembershipStatus.CONFIRMED:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Confirmá tu asistencia antes de votar")
    if table.planned_games_count is not None and len(payload.game_ids) > table.planned_games_count:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Podés votar hasta {table.planned_games_count} juego(s)",
        )

    _require_existing_games(db, payload.game_ids)

    participant.votes = payload.game_ids
    db.commit()
    db.refresh(table)
    return table


@router.post("/{table_id}/resolve", response_model=TableRead)
def resolve_table(
    table_id: uuid.UUID,
    payload: ResolveTable,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> GameTable:
    table = _get_table(db, table_id)
    _require_host(table, current_user.id)

    if table.status != TableStatus.VOTING:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "La mesa no está en etapa de votación")

    _require_existing_games(db, payload.result_game_ids)

    table.result_game_ids = payload.result_game_ids
    table.result_was_tie = payload.result_was_tie
    table.status = TableStatus.RESOLVED
    db.commit()
    db.refresh(table)
    return table


@router.post("/{table_id}/cancel", response_model=TableRead)
def cancel_table(
    table_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> GameTable:
    table = _get_table(db, table_id)
    _require_host(table, current_user.id)

    if table.status in (TableStatus.RESOLVED, TableStatus.CANCELLED):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "La mesa ya está cerrada")

    table.status = TableStatus.CANCELLED
    db.commit()
    db.refresh(table)
    return table
