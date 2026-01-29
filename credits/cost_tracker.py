"""Estimate and record API costs per story."""

from sqlalchemy.orm import Session

from credits.pricing import (
    COST_DALLE3_PER_IMAGE,
    COST_GPT4O_PER_1K_INPUT,
    COST_GPT4O_PER_1K_OUTPUT,
    COST_TTS_PER_1M_CHARS,
)
from db.models import Story


def estimate_story_generation_cost(
    prompt_tokens: int, completion_tokens: int
) -> float:
    """Estimate GPT-4o cost from token counts."""
    return (
        (prompt_tokens / 1000) * COST_GPT4O_PER_1K_INPUT
        + (completion_tokens / 1000) * COST_GPT4O_PER_1K_OUTPUT
    )


def estimate_cover_cost() -> float:
    return COST_DALLE3_PER_IMAGE


def estimate_tts_cost(total_chars: int) -> float:
    return (total_chars / 1_000_000) * COST_TTS_PER_1M_CHARS


def record_costs(
    db: Session,
    story_id: str,
    cost_story_generation: float,
    cost_cover_image: float,
    cost_tts: float,
    segment_count: int,
    total_tts_chars: int,
):
    """Update a story record with cost data."""
    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:
        return

    story.cost_story_generation = round(cost_story_generation, 6)
    story.cost_cover_image = round(cost_cover_image, 6)
    story.cost_tts = round(cost_tts, 6)
    story.cost_total = round(
        cost_story_generation + cost_cover_image + cost_tts, 6
    )
    story.segment_count = segment_count
    story.total_tts_chars = total_tts_chars
    db.commit()
