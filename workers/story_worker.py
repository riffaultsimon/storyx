import logging
import os
from concurrent.futures import ThreadPoolExecutor

from config import STORAGE_DIR
from db.session import SessionLocal
from db.models import Story
from story.schema import StructuredStory
from tts.pipeline import synthesize_story
from audio.assembler import assemble_audio

logger = logging.getLogger(__name__)

_executor = ThreadPoolExecutor(max_workers=1)


def submit_tts_job(story_id: str, structured_story: StructuredStory):
    """Submit a TTS generation job to the background executor."""
    _executor.submit(_process_tts, story_id, structured_story)
    logger.info("Submitted TTS job for story %s", story_id)


def _process_tts(story_id: str, structured_story: StructuredStory):
    """Background task: synthesize TTS segments and assemble MP3."""
    db = SessionLocal()
    try:
        story = db.query(Story).filter(Story.id == story_id).first()
        if not story:
            logger.error("Story %s not found", story_id)
            return

        # Ensure output directory exists
        audio_dir = os.path.join(STORAGE_DIR, "audio")
        os.makedirs(audio_dir, exist_ok=True)

        output_path = os.path.join(audio_dir, f"{story_id}.mp3")

        # Synthesize all segments
        logger.info("Starting TTS synthesis for story %s", story_id)
        segments, total_tts_chars = synthesize_story(structured_story)

        # Assemble into MP3
        duration = assemble_audio(segments, output_path)

        # Record TTS cost data
        from credits.cost_tracker import estimate_tts_cost, record_costs
        cost_tts = estimate_tts_cost(total_tts_chars)
        story.total_tts_chars = total_tts_chars
        story.cost_tts = round(cost_tts, 6)
        story.cost_total = round(
            (story.cost_story_generation or 0)
            + (story.cost_cover_image or 0)
            + cost_tts, 6
        )

        # Update story record
        story.audio_path = output_path
        story.duration_seconds = duration
        story.status = "ready"
        db.commit()
        logger.info("Story %s TTS complete: %.1f seconds", story_id, duration)

    except Exception as e:
        logger.exception("TTS processing failed for story %s: %s", story_id, e)
        try:
            story = db.query(Story).filter(Story.id == story_id).first()
            if story:
                story.status = "failed"
                db.commit()
        except Exception:
            db.rollback()
    finally:
        db.close()
