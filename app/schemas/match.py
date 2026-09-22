import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class MatchCreate(BaseModel):
    table_id: uuid.UUID | None = None
    game_id: uuid.UUID
    participant_ids: list[uuid.UUID] = Field(min_length=1)
    date: date
    duration: str | None = Field(default=None, max_length=50)
    location: str | None = Field(default=None, max_length=200)
    comment: str | None = Field(default=None, max_length=1000)
    photo_urls: list[str] | None = None
    scores: dict[str, int] | None = None

    winner_id: uuid.UUID | None = None
    is_tie: bool = False
    tied_ids: list[uuid.UUID] | None = None
    is_group_win: bool = False
    group_win_ids: list[uuid.UUID] | None = None


class MatchRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    table_id: uuid.UUID | None
    game_id: uuid.UUID
    logged_by_id: uuid.UUID
    participant_ids: list[uuid.UUID]
    winner_id: uuid.UUID | None
    is_tie: bool
    tied_ids: list[uuid.UUID] | None
    is_group_win: bool
    group_win_ids: list[uuid.UUID] | None
    scores: dict[str, int] | None
    date: date
    duration: str | None
    location: str | None
    comment: str | None
    photo_urls: list[str] | None
    created_at: datetime
