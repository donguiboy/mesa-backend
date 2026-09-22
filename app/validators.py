import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.game import Game
from app.models.user import User


def require_existing_users(db: Session, user_ids: list[uuid.UUID]) -> None:
    found = set(db.scalars(select(User.id).where(User.id.in_(user_ids))))
    missing = set(user_ids) - found
    if missing:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Usuario(s) no encontrado(s): {missing}")


def require_existing_games(db: Session, game_ids: list[uuid.UUID]) -> None:
    found = set(db.scalars(select(Game.id).where(Game.id.in_(game_ids))))
    missing = set(game_ids) - found
    if missing:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Juego(s) no encontrado(s): {missing}")
