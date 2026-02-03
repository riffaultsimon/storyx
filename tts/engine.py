import logging

from openai import OpenAI

from config import OPENAI_API_KEY, TTS_MODEL, TTS_RESPONSE_FORMAT, TTS_SPEED

logger = logging.getLogger(__name__)

_client = OpenAI(api_key=OPENAI_API_KEY)


def synthesize(text: str, voice: str, instructions: str, model_override: str | None = None) -> bytes:
    """Synthesize speech via the OpenAI TTS API.

    Args:
        text: The text to speak.
        voice: OpenAI voice name (alloy, ash, ballad, coral, echo, fable, nova, onyx, sage, shimmer).
        instructions: Style/emotion instruction for gpt-4o-mini-tts.
        model_override: Optional model name to use instead of the default.

    Returns:
        Raw audio bytes in the configured format (MP3).
    """
    model = model_override or TTS_MODEL

    response = _client.audio.speech.create(
        model=model,
        voice=voice,
        input=text,
        instructions=instructions,
        response_format=TTS_RESPONSE_FORMAT,
        speed=TTS_SPEED,
    )

    audio_bytes = response.content
    logger.info("Synthesized %d bytes for voice=%s", len(audio_bytes), voice)
    return audio_bytes
