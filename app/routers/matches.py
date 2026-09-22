import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import get_current_user
from app.models.enums import TableStatus
from app.models.game_table import GameTable
from app.models.match import Match
from app.models.user import User
from app.schemas.match import MatchCreate, MatchRead
from app.validators import require_existing_games, require_existing_users

router = APIRouter(prefix="/matches", tags=["matches"])


def _validate_outcome(payload: MatchCreate) -> None:
    participants = set(payload.participant_ids)
    outcomes = [payload.winner_id is not None, payload.is_tie, payload.is_group_win]

    if sum(outcomes) != 1:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Especificá exactamente un resultado: ganador único, empate o victoria grupal",
        )

    if payload.winner_id is not None and payload.winner_id not in participants:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "El ganador debe ser un participante")

    if payload.is_tie:
        if not payload.tied_ids or len(payload.tied_ids) < 2:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Un empate necesita al menos 2 jugadores")
        if not set(payload.tied_ids) <= participants:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Los empatados deben ser participantes")

    if payload.is_group_win:
        if not payload.group_win_ids or len(payload.group_win_ids) < 2:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, "Una victoria grupal necesita al menos 2 jugadores"
            )
        if not set(payload.group_win_ids) <= participants:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, "El grupo ganador debe ser participante"
            )


def _validate_table_link(db: Session, payload: MatchCreate, current_user: User) -> GameTable | None:
    if payload.table_id is None:
        return None

    table = db.get(GameTable, payload.table_id)
    if table is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Mesa no encontrada")
    if current_user.id not in {p.player_id for p in table.participants}:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "No sos parte de esta mesa")
    if table.status != TableStatus.RESOLVED:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "La mesa todavía no está resuelta")
    if table.logged_match_id is not None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Esta mesa ya tiene una partida registrada")
    if not set(payload.participant_ids) <= {p.player_id for p in table.participants}:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Los participantes deben pertenecer a la mesa"
        )
    return table


@router.post("", response_model=MatchRead, status_code=status.HTTP_201_CREATED)
def create_match(
    payload: MatchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Match:
    if current_user.id not in payload.participant_ids:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Solo podés registrar partidas en las que jugaste")

    _validate_outcome(payload)
    require_existing_users(db, payload.participant_ids)
    require_existing_games(db, [payload.game_id])
    table = _validate_table_link(db, payload, current_user)

    match = Match(
        table_id=payload.table_id,
        game_id=payload.game_id,
        logged_by_id=current_user.id,
        participant_ids=payload.participant_ids,
        winner_id=payload.winner_id,
        is_tie=payload.is_tie,
        tied_ids=payload.tied_ids,
        is_group_win=payload.is_group_win,
        group_win_ids=payload.group_win_ids,
        scores=payload.scores,
        date=payload.date,
        duration=payload.duration,
        location=payload.location,
        comment=payload.comment,
        photo_urls=payload.photo_urls,
    )
    db.add(match)
    db.flush()

    if table is not None:
        table.logged_match_id = match.id

    db.commit()
    db.refresh(match)
    return match


@router.get("", response_model=list[MatchRead])
def list_my_matches(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Match]:
    return list(
        db.scalars(
            select(Match)
            .where(Match.participant_ids.any(current_user.id))
            .order_by(Match.date.desc())
        )
    )


@router.get("/{match_id}", response_model=MatchRead)
def get_match(
    match_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Match:
    match = db.get(Match, match_id)
    if match is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Partida no encontrada")
    if current_user.id not in match.participant_ids:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "No fuiste parte de esta partida")
    return match
