import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, func
from sqlalchemy.dialects.postgresql import ARRAY, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Game(Base):
    """Catálogo de juegos. Los campos de BGG (descripción, mecánicas,
    imagen, etc.) se completan al importar el dataset — ver
    scripts/import_bgg_games.py. Un juego creado a mano (POST /games)
    solo tiene `name`."""

    __tablename__ = "games"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)

    # id del juego en BoardGameGeek (p. ej. "bgg-13"); único para poder
    # reimportar el dataset sin duplicar filas.
    bgg_id: Mapped[str | None] = mapped_column(String(50), unique=True, nullable=True)

    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    players: Mapped[str | None] = mapped_column(String(20), nullable=True)
    duration: Mapped[str | None] = mapped_column(String(50), nullable=True)
    complexity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    categories: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    mechanics: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    themes: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    tags: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    image: Mapped[str | None] = mapped_column(String(500), nullable=True)
    rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    year_published: Mapped[int | None] = mapped_column(Integer, nullable=True)
    min_age: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # placeholders de portada usados por el frontend cuando no hay `image`
    gradient: Mapped[str | None] = mapped_column(String(150), nullable=True)
    emoji: Mapped[str | None] = mapped_column(String(16), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
