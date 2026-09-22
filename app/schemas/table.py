import uuid
from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import MembershipStatus, ParticipantRole, ProposalStatus, TableStatus


class TableCreate(BaseModel):
    date: date
    time: time
    planned_games_count: int | None = Field(default=None, ge=1)
    vibe_genres: list[str] | None = Field(default=None, max_length=3)
    description: str | None = Field(default=None, max_length=500)
    participant_ids: list[uuid.UUID] = Field(default_factory=list)


class InviteParticipants(BaseModel):
    participant_ids: list[uuid.UUID] = Field(min_length=1)


class RespondInvite(BaseModel):
    confirm: bool


class ProposeGames(BaseModel):
    game_ids: list[uuid.UUID] = Field(min_length=1)


class VoteGames(BaseModel):
    game_ids: list[uuid.UUID] = Field(min_length=1)


class ResolveTable(BaseModel):
    result_game_ids: list[uuid.UUID] = Field(min_length=1)
    result_was_tie: bool = False


class ParticipantRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    player_id: uuid.UUID
    role: ParticipantRole
    membership_status: MembershipStatus
    proposal_status: ProposalStatus
    proposed_game_ids: list[uuid.UUID] | None = None
    votes: list[uuid.UUID] | None = None


class TableRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    host_id: uuid.UUID
    date: date
    time: time
    status: TableStatus
    planned_games_count: int | None
    vibe_genres: list[str] | None
    description: str | None
    result_game_ids: list[uuid.UUID] | None
    result_was_tie: bool
    logged_match_id: uuid.UUID | None
    created_at: datetime
    participants: list[ParticipantRead]
