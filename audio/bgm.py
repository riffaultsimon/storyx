"""Background music generation using Google Lyria 2 (Vertex AI) and overlay mixing."""

import base64
import io
import logging
import os

import requests
from pydub import AudioSegment

from config import (
    GOOGLE_CLOUD_LOCATION,
    GOOGLE_CLOUD_PROJECT,
    GOOGLE_SERVICE_ACCOUNT_FILE,
    STORAGE_DIR,
)

logger = logging.getLogger(__name__)

# Mood to music prompt mapping
MOOD_MUSIC_PROMPTS = {
    "adventurous": "upbeat adventurous children's orchestral music, playful and exciting, major key",
    "funny": "lighthearted quirky children's music, comedic pizzicato strings, bouncy xylophone",
    "heartwarming": "gentle warm children's music, soft piano and strings, tender and emotional",
    "mysterious": "mysterious whimsical children's music, soft woodwinds, curious and magical",
    "educational": "cheerful bright children's learning music, friendly ukulele and glockenspiel",
    "calming": "soft calming lullaby music, gentle acoustic guitar, peaceful and soothing",
}

DEFAULT_PROMPT = "gentle cheerful children's background music, soft and pleasant"

# BGM volume reduction in dB (relative to narration)
BGM_VOLUME_DB = -20


def generate_bgm(mood: str, duration_seconds: float, story_id: str) -> str | None:
    """Generate background music via Lyria 2 and save as MP3.

    Args:
        mood: Story mood for prompt selection.
        duration_seconds: Target duration of the BGM track.
        story_id: Used for the output filename.

    Returns:
        Local file path to the generated BGM MP3, or None on failure.
    """
    try:
        import google.auth.transport.requests
        from google.oauth2 import service_account

        prompt = MOOD_MUSIC_PROMPTS.get(mood, DEFAULT_PROMPT)
        prompt += ", instrumental only, no vocals"

        # Authenticate via service account
        credentials = service_account.Credentials.from_service_account_file(
            GOOGLE_SERVICE_ACCOUNT_FILE,
            scopes=["https://www.googleapis.com/auth/cloud-platform"],
        )
        credentials.refresh(google.auth.transport.requests.Request())

        # Call Lyria 2 predict endpoint on Vertex AI
        endpoint = (
            f"https://{GOOGLE_CLOUD_LOCATION}-aiplatform.googleapis.com/v1/"
            f"projects/{GOOGLE_CLOUD_PROJECT}/locations/{GOOGLE_CLOUD_LOCATION}/"
            f"publishers/google/models/lyria-002:predict"
        )
        payload = {
            "instances": [
                {
                    "prompt": prompt,
                    "negative_prompt": "vocals, singing, speech, voice, lyrics",
                }
            ],
        }
        headers = {
            "Authorization": f"Bearer {credentials.token}",
            "Content-Type": "application/json",
        }

        resp = requests.post(endpoint, headers=headers, json=payload)
        if not resp.ok:
            logger.error(
                "Lyria 2 API error %s for story %s: %s",
                resp.status_code, story_id, resp.text,
            )
            return None
        predictions = resp.json().get("predictions", [])

        if not predictions:
            logger.error("Lyria 2 returned no predictions for story %s", story_id)
            return None

        audio_data = base64.b64decode(predictions[0]["bytesBase64Encoded"])

        bgm_dir = os.path.join(STORAGE_DIR, "bgm")
        os.makedirs(bgm_dir, exist_ok=True)
        bgm_path = os.path.join(bgm_dir, f"{story_id}.mp3")

        # Convert to MP3 via pydub (Lyria outputs WAV/PCM)
        audio_segment = AudioSegment.from_file(io.BytesIO(audio_data))
        audio_segment.export(bgm_path, format="mp3", codec="libmp3lame", bitrate="192k")

        logger.info("Generated BGM for story %s: %s", story_id, bgm_path)
        return bgm_path

    except Exception as e:
        logger.error("BGM generation failed for story %s: %s", story_id, e)
        return None


def mix_bgm(narration_path: str, bgm_path: str, output_path: str, tags: dict | None = None) -> float:
    """Overlay BGM under narration audio and export.

    The BGM is looped/trimmed to match the narration length and reduced in volume.

    Args:
        narration_path: Path to the narration MP3.
        bgm_path: Path to the BGM MP3.
        output_path: Path to write the final mixed MP3.
        tags: Optional ID3 metadata tags (e.g. title, artist, album).

    Returns:
        Duration in seconds of the final audio.
    """
    narration = AudioSegment.from_mp3(narration_path)
    bgm = AudioSegment.from_mp3(bgm_path)

    # Loop BGM if shorter than narration
    narration_len = len(narration)
    if len(bgm) < narration_len:
        repeats = (narration_len // len(bgm)) + 1
        bgm = bgm * repeats

    # Trim to narration length and reduce volume
    bgm = bgm[:narration_len]
    bgm = bgm + BGM_VOLUME_DB

    # Add fade in/out to BGM
    bgm = bgm.fade_in(2000).fade_out(3000)

    mixed = narration.overlay(bgm)
    export_kwargs = {
        "format": "mp3",
        "codec": "libmp3lame",
        "bitrate": "192k",
        "parameters": ["-q:a", "0"],
    }
    if tags:
        export_kwargs["tags"] = tags
    mixed.export(output_path, **export_kwargs)

    duration = len(mixed) / 1000.0
    logger.info("Mixed BGM into narration: %.1f seconds -> %s", duration, output_path)
    return duration
