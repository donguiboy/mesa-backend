import uuid
from datetime import date as date_, datetime, time as time_

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Time, func
from sqlalchemy.dialects.postgresql import ARRAY, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import TableStatus


class GameTable(Base):
    """Una "mesa": una juntada propuesta por un host, con invitados que
    proponen y votan juegos hasta que se resuelve qué se juega."""

    __tablename__ = "game_tables"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    host_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    date: Mapped[date_] = mapped_column(Date, nullable=False)
    time: Mapped[time_] = mapped_column(Time, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=TableStatus.PROPOSING)

    planned_games_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    vibe_genres: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    result_game_ids: Mapped[list[uuid.UUID] | None] = mapped_column(
        ARRAY(PGUUID(as_uuid=True)), nullable=True
    )
    result_was_tie: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # use_alter: rompe el ciclo game_tables <-> matches para create_all/drop_all
    # (coincide con la migración, que agrega esta FK en un ALTER TABLE separado).
    logged_match_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "matches.id", use_alter=True, name="fk_game_tables_logged_match_id_matches"
        ),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    participants: Mapped[list["TableParticipant"]] = relationship(
        back_populates="table", cascade="all, delete-orphan"
    )
