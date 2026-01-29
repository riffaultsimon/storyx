import logging

from story.schema import StructuredStory, Segment
from tts.engine import synthesize
from tts.voice_mapper import (
    build_narrator_instruction,
    build_voice_instruction,
    get_narrator_voice,
    pick_voice,
)

logger = logging.getLogger(__name__)


def synthesize_story(story: StructuredStory) -> tuple[list[dict], int]:
    """Synthesize all segments of a story via OpenAI TTS.

    Returns a tuple of:
    - list of dicts: [{"audio_bytes": bytes, "pause_after_ms": int}, ...]
    - total_tts_chars: int — total characters sent to TTS
    """
    char_map = {ch.name: ch for ch in story.characters}

    results = []
    total = len(story.segments)
    total_tts_chars = 0

    for i, segment in enumerate(story.segments):
        logger.info("Synthesizing segment %d/%d (type=%s)", i + 1, total, segment.type)

        voice, instructions = _resolve_voice(segment, char_map)
        total_tts_chars += len(segment.text)

        try:
            audio_bytes = synthesize(segment.text, voice, instructions)
            results.append({
                "audio_bytes": audio_bytes,
                "pause_after_ms": segment.pause_after_ms,
            })
        except Exception as e:
            logger.error("Failed to synthesize segment %d: %s", segment.segment_id, e)
            results.append({
                "audio_bytes": b"",
                "pause_after_ms": segment.pause_after_ms,
            })

    return results, total_tts_chars


def _resolve_voice(segment: Segment, char_map: dict) -> tuple[str, str]:
    """Return (voice_name, instructions) for a segment."""
    if segment.type == "narration" or segment.character is None:
        return get_narrator_voice(), build_narrator_instruction(segment.emotion)

    character = char_map.get(segment.character)
    if character is None:
        return get_narrator_voice(), build_narrator_instruction(segment.emotion)

    return pick_voice(character), build_voice_instruction(character, segment.emotion)
