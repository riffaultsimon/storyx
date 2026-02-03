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


def synthesize_story(
    story: StructuredStory,
    tts_model: str | None = None,
    recordings: dict[int, str] | None = None,
    language: str = "en",
) -> tuple[list[dict], int]:
    """Synthesize all segments of a story via OpenAI TTS.

    Args:
        story: The structured story to synthesize.
        tts_model: Optional TTS model override.
        recordings: Optional mapping of segment_id → WAV file path for
            user-recorded segments that should skip TTS.
        language: Language code for voice selection (en, fr, de, es).

    Returns a tuple of:
    - list of dicts: [{"audio_bytes": bytes, "pause_after_ms": int, "format": str}, ...]
    - total_tts_chars: int — total characters sent to TTS
    """
    char_map = {ch.name: ch for ch in story.characters}
    recordings = recordings or {}
    _current_language = language

    results = []
    total = len(story.segments)
    total_tts_chars = 0

    for i, segment in enumerate(story.segments):
        logger.info("Synthesizing segment %d/%d (type=%s)", i + 1, total, segment.type)

        # Check if user recorded this segment
        rec_path = recordings.get(segment.segment_id)
        if rec_path:
            try:
                with open(rec_path, "rb") as f:
                    wav_bytes = f.read()
                logger.info("Using user recording for segment %d", segment.segment_id)
                results.append({
                    "audio_bytes": wav_bytes,
                    "pause_after_ms": segment.pause_after_ms,
                    "format": "wav",
                })
                continue
            except Exception as e:
                logger.warning(
                    "Failed to read recording for segment %d, falling back to TTS: %s",
                    segment.segment_id, e,
                )

        voice, instructions = _resolve_voice(segment, char_map, _current_language)
        total_tts_chars += len(segment.text)

        try:
            audio_bytes = synthesize(segment.text, voice, instructions, model_override=tts_model)
            results.append({
                "audio_bytes": audio_bytes,
                "pause_after_ms": segment.pause_after_ms,
                "format": "mp3",
            })
        except Exception as e:
            logger.error("Failed to synthesize segment %d: %s", segment.segment_id, e)
            results.append({
                "audio_bytes": b"",
                "pause_after_ms": segment.pause_after_ms,
                "format": "mp3",
            })

    return results, total_tts_chars


def _resolve_voice(segment: Segment, char_map: dict, language: str = "en") -> tuple[str, str]:
    """Return (voice_name, instructions) for a segment."""
    if segment.type == "narration" or segment.character is None:
        return get_narrator_voice(language), build_narrator_instruction(segment.emotion)

    character = char_map.get(segment.character)
    if character is None:
        return get_narrator_voice(language), build_narrator_instruction(segment.emotion)

    return pick_voice(character, language), build_voice_instruction(character, segment.emotion)
