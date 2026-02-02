import logging
import os

import requests

from config import STORAGE_DIR

logger = logging.getLogger(__name__)


def _ensure_dir(subdir: str) -> str:
    path = os.path.join(STORAGE_DIR, subdir)
    os.makedirs(path, exist_ok=True)
    return path


def download_and_save_image(url: str, story_id: str) -> str:
    """Download an image from a URL and save it locally.

    Returns the local file path.
    """
    img_dir = _ensure_dir("covers")
    file_path = os.path.join(img_dir, f"{story_id}.png")

    response = requests.get(url, timeout=60)
    response.raise_for_status()

    with open(file_path, "wb") as f:
        f.write(response.content)

    logger.info("Saved cover image: %s", file_path)
    return file_path


def get_audio_path(story_id: str) -> str | None:
    """Return the audio file path if it exists."""
    path = os.path.join(STORAGE_DIR, "audio", f"{story_id}.mp3")
    return path if os.path.exists(path) else None


def get_cover_path(story_id: str) -> str | None:
    """Return the cover image path if it exists."""
    path = os.path.join(STORAGE_DIR, "covers", f"{story_id}.png")
    return path if os.path.exists(path) else None


def save_recording(story_id: str, segment_id: int, audio_bytes: bytes) -> str:
    """Write a user voice recording to disk and return the file path."""
    rec_dir = _ensure_dir(os.path.join("recordings", story_id))
    file_path = os.path.join(rec_dir, f"{segment_id}.wav")
    with open(file_path, "wb") as f:
        f.write(audio_bytes)
    logger.info("Saved recording: %s", file_path)
    return file_path


def read_file_bytes(path: str) -> bytes | None:
    """Read a file and return its bytes, or None if not found."""
    if path and os.path.exists(path):
        with open(path, "rb") as f:
            return f.read()
    return None
