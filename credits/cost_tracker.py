"""Estimate and record API costs per story."""

from sqlalchemy.orm import Session

from credits.pricing import (
    COVER_PRICING,
    LLM_PRICING,
    TTS_PRICING,
)
from db.models import Story


def estimate_story_generation_cost(
    prompt_tokens: int, completion_tokens: int, model: str = "gpt-4o"
) -> float:
    """Estimate LLM cost from token counts and model name."""
    input_rate, output_rate = LLM_PRICING.get(
        model, LLM_PRICING["gpt-4o"]
    )
    return (
        (prompt_tokens / 1000) * input_rate
        + (completion_tokens / 1000) * output_rate
    )


def estimate_cover_cost(provider: str = "dalle3") -> float:
    return COVER_PRICING.get(provider, COVER_PRICING["dalle3"])


def estimate_tts_cost(total_chars: int, model: str = "gpt-4o-mini-tts") -> float:
    rate = TTS_PRICING.get(model, TTS_PRICING["gpt-4o-mini-tts"])
    return (total_chars / 1_000_000) * rate


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
