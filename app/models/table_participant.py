import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import ARRAY, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import MembershipStatus, ProposalStatus


class TableParticipant(Base):
    """Participación de un usuario en una mesa: rol, si confirmó la invitación,
    y los juegos que propuso/votó."""

    __tablename__ = "table_participants"
    __table_args__ = (UniqueConstraint("table_id", "player_id", name="uq_table_player"),)

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    table_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("game_tables.id"), nullable=False
    )
    player_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )

    role: Mapped[str] = mapped_column(String(10), nullable=False)
    membership_status: Mapped[str] = mapped_column(
        String(15), nullable=False, default=MembershipStatus.INVITED
    )
    proposal_status: Mapped[str] = mapped_column(
        String(10), nullable=False, default=ProposalStatus.PENDING
    )

    proposed_game_ids: Mapped[list[uuid.UUID] | None] = mapped_column(
        ARRAY(PGUUID(as_uuid=True)), nullable=True
    )
    votes: Mapped[list[uuid.UUID] | None] = mapped_column(ARRAY(PGUUID(as_uuid=True)), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    table: Mapped["GameTable"] = relationship(back_populates="participants")
