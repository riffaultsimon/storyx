from pydantic import BaseModel, Field


class CharacterProfile(BaseModel):
    name: str
    age: int | None = None
    gender: str | None = None
    description: str = ""
    default_emotion: str = "neutral"


class Segment(BaseModel):
    segment_id: int
    type: str = Field(pattern=r"^(narration|dialog)$")
    character: str | None = None
    emotion: str = "neutral"
    text: str
    pause_after_ms: int = 400


class StructuredStory(BaseModel):
    title: str
    summary: str
    characters: list[CharacterProfile]
    segments: list[Segment]
    moral: str | None = None
