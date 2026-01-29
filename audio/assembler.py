import io
import logging

from pydub import AudioSegment

logger = logging.getLogger(__name__)


def assemble_audio(segments: list[dict], output_path: str) -> float:
    """Concatenate synthesized audio segments with pauses into a single MP3.

    Args:
        segments: List of dicts with "audio_bytes" (MP3 bytes) and "pause_after_ms".
        output_path: Path to write the final MP3 file.

    Returns:
        Duration in seconds.
    """
    combined = AudioSegment.silent(duration=0)

    for seg in segments:
        audio_bytes = seg["audio_bytes"]
        pause_ms = seg.get("pause_after_ms", 400)

        if not audio_bytes:
            # Failed segment — insert short silence
            combined += AudioSegment.silent(duration=500)
        else:
            audio_segment = AudioSegment.from_file(io.BytesIO(audio_bytes), format="mp3")
            combined += audio_segment

        if pause_ms > 0:
            combined += AudioSegment.silent(duration=pause_ms)

    combined.export(output_path, format="mp3", bitrate="192k")

    duration_seconds = len(combined) / 1000.0
    logger.info("Assembled audio: %.1f seconds -> %s", duration_seconds, output_path)
    return duration_seconds
