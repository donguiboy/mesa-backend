from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import get_current_user
from app.models.game import Game
from app.models.user import User
from app.schemas.game import GameCreate, GameRead

router = APIRouter(prefix="/games", tags=["games"])


@router.get("", response_model=list[GameRead])
def list_games(db: Session = Depends(get_db)) -> list[Game]:
    return list(db.scalars(select(Game).order_by(Game.name)))


@router.post("", response_model=GameRead, status_code=status.HTTP_201_CREATED)
def create_game(
    payload: GameCreate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> Game:
    game = Game(name=payload.name)
    db.add(game)
    db.commit()
    db.refresh(game)
    return game
