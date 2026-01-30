import io
import logging

from pydub import AudioSegment

logger = logging.getLogger(__name__)


def assemble_audio(segments: list[dict], output_path: str, tags: dict | None = None) -> float:
    """Concatenate synthesized audio segments with pauses into a single MP3.

    Args:
        segments: List of dicts with "audio_bytes" (MP3 bytes) and "pause_after_ms".
        output_path: Path to write the final MP3 file.
        tags: Optional ID3 metadata tags (e.g. title, artist, album).

    Returns:
        Duration in seconds.
    """
    combined = None

    for seg in segments:
        audio_bytes = seg["audio_bytes"]
        pause_ms = seg.get("pause_after_ms", 400)

        if not audio_bytes:
            chunk = AudioSegment.silent(duration=500)
        else:
            chunk = AudioSegment.from_file(io.BytesIO(audio_bytes), format="mp3")

        # Initialise combined from first real segment to inherit its sample rate/channels
        if combined is None:
            combined = chunk
        else:
            combined += chunk

        if pause_ms > 0:
            # Generate silence matching the audio properties
            silence = AudioSegment.silent(
                duration=pause_ms,
                frame_rate=combined.frame_rate,
            )
            combined += silence

    if combined is None:
        combined = AudioSegment.silent(duration=500)

    export_kwargs = {
        "format": "mp3",
        "codec": "libmp3lame",
        "bitrate": "192k",
        "parameters": ["-q:a", "0"],
    }
    if tags:
        export_kwargs["tags"] = tags
    combined.export(output_path, **export_kwargs)

    duration_seconds = len(combined) / 1000.0
    logger.info("Assembled audio: %.1f seconds -> %s", duration_seconds, output_path)
    return duration_seconds
