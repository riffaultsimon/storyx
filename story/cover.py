"""Cover image generation — supports DALL-E 3 and Imagen 3 (Google)."""

import base64
import logging
import os

from config import (
    OPENAI_API_KEY,
    COVER_MODEL,
    COVER_SIZE,
    COVER_STYLE,
    STORAGE_DIR,
)

logger = logging.getLogger(__name__)


def _build_prompt(summary: str) -> str:
    return (
        f"A wordless children's book illustration with zero text anywhere. "
        f"Scene: {summary}. "
        "Style: hand-painted watercolor cartoon, vibrant pastel colors, friendly characters, "
        "rounded shapes, magical atmosphere, suitable for young children. "
        "CRITICAL: This is a purely visual, textless illustration — "
        "there are no words, letters, numbers, titles, labels, signs, banners, "
        "speech bubbles, captions, or any form of writing visible anywhere in the image. "
        "Every surface is clean of typography."
    )


def generate_cover_image(summary: str, title: str = "", provider: str = "dalle3") -> str:
    """Generate a cover image and return its URL or local path.

    Args:
        summary: Story summary describing the scene.
        title: Kept for API compatibility (not used in prompts to avoid text in images).
        provider: "dalle3" or "imagen3"

    Returns:
        URL (for dalle3) or local file path (for imagen3).
    """
    if provider == "imagen3":
        return _generate_imagen3(summary, title)
    return _generate_dalle3(summary, title)


def _generate_dalle3(summary: str, title: str) -> str:
    """Generate via OpenAI DALL-E 3. Returns image URL."""
    from openai import OpenAI

    client = OpenAI(api_key=OPENAI_API_KEY)
    prompt = _build_prompt(summary)

    response = client.images.generate(
        model=COVER_MODEL,
        prompt=prompt,
        size=COVER_SIZE,
        style=COVER_STYLE,
        n=1,
    )

    image_url = response.data[0].url
    logger.info("Generated DALL-E 3 cover for '%s'", title)
    return image_url


def _generate_imagen3(summary: str, title: str) -> str:
    """Generate via Google Imagen 3 through Vertex AI. Returns local file path."""
    from google.genai import types
    from config import get_google_client

    client = get_google_client()
    prompt = _build_prompt(summary)

    response = client.models.generate_images(
        model="imagen-3.0-generate-002",
        prompt=prompt,
        config=types.GenerateImagesConfig(
            number_of_images=1,
            aspect_ratio="1:1",
            safety_filter_level="BLOCK_ONLY_HIGH",
            negative_prompt="text, letters, words, title, writing, typography, captions, watermark",
        ),
    )

    if not response.generated_images:
        # Log the full response to diagnose filtering or other issues
        logger.warning("Imagen 3 returned no images for '%s'. Response: %s", title, response)
        raise RuntimeError("Imagen 3 returned no images")

    image_bytes = response.generated_images[0].image.image_bytes

    # Save directly to covers dir
    covers_dir = os.path.join(STORAGE_DIR, "covers")
    os.makedirs(covers_dir, exist_ok=True)

    import uuid
    temp_name = f"imagen_{uuid.uuid4().hex[:12]}.png"
    file_path = os.path.join(covers_dir, temp_name)
    with open(file_path, "wb") as f:
        f.write(image_bytes)

    logger.info("Generated Imagen 3 cover for '%s' -> %s", title, file_path)
    return file_path
