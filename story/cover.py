import logging

from openai import OpenAI

from config import OPENAI_API_KEY, COVER_MODEL, COVER_SIZE, COVER_STYLE

logger = logging.getLogger(__name__)

client = OpenAI(api_key=OPENAI_API_KEY)


def generate_cover_image(summary: str, title: str) -> str:
    """Generate a cover image via DALL-E 3 and return the image URL."""
    prompt = (
        f"A colorful, whimsical children's book cover illustration for a story titled '{title}'. "
        f"Scene: {summary}. "
        "Style: cartoon, vibrant pastel colors, friendly characters, "
        "rounded shapes, magical atmosphere, suitable for young children. "
        "No text or letters in the image."
    )

    response = client.images.generate(
        model=COVER_MODEL,
        prompt=prompt,
        size=COVER_SIZE,
        style=COVER_STYLE,
        n=1,
    )

    image_url = response.data[0].url
    logger.info("Generated cover image for '%s'", title)
    return image_url
