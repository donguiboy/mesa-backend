import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class GameCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)


class GameRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    bgg_id: str | None
    description: str | None
    players: str | None
    duration: str | None
    complexity: int | None
    category: str | None
    categories: list[str] | None
    mechanics: list[str] | None
    themes: list[str] | None
    tags: list[str] | None
    image: str | None
    rating: float | None
    year_published: int | None
    min_age: int | None
    gradient: str | None
    emoji: str | None
    created_at: datetime
