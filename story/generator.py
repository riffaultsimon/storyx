import json
import logging

from openai import OpenAI

from config import OPENAI_API_KEY, STORY_MODEL, EMOTIONS
from story.schema import StructuredStory

logger = logging.getLogger(__name__)

client = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = """\
You are a world-class children's story writer. You create vivid, age-appropriate stories \
with memorable characters, engaging dialog, and gentle morals.

You MUST respond with a single JSON object matching this exact schema:

{
  "title": "string",
  "summary": "A 2-3 sentence summary of the story suitable for generating a cover illustration",
  "characters": [
    {
      "name": "string",
      "age": integer,
      "gender": "male" or "female",
      "description": "short physical/personality description",
      "default_emotion": "one of: EMOTIONS_LIST"
    }
  ],
  "segments": [
    {
      "segment_id": integer (starting from 1),
      "type": "narration" or "dialog",
      "character": "character name or null for narration",
      "emotion": "one of: EMOTIONS_LIST",
      "text": "the spoken or narrated text",
      "pause_after_ms": integer (200-800)
    }
  ],
  "moral": "string or null"
}

Rules:
- For narration segments, set character to null and type to "narration"
- For dialog segments, set character to the speaking character's name and type to "dialog"
- Vary emotions naturally throughout the story
- Use appropriate pauses: shorter (200ms) mid-dialog, longer (600-800ms) between scenes
- Keep language age-appropriate for the specified age range
- Include a narrator character in the characters list with name "Narrator"
""".replace("EMOTIONS_LIST", ", ".join(EMOTIONS))


def generate_story(
    topic: str,
    setting: str,
    mood: str,
    age_range: str,
    story_length: str,
) -> tuple[StructuredStory, dict]:
    length_guide = {
        "short": "8-12 segments",
        "medium": "15-25 segments",
        "long": "30-45 segments",
    }

    user_prompt = (
        f"Write a {mood} children's story about '{topic}' "
        f"set in {setting}. "
        f"Target age range: {age_range} years old. "
        f"Story length: {story_length} ({length_guide.get(story_length, '15-25 segments')}). "
        f"Include at least 2-3 named characters with dialog."
    )

    response = client.chat.completions.create(
        model=STORY_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.9,
        max_tokens=4096,
    )

    raw = response.choices[0].message.content
    data = json.loads(raw)
    story = StructuredStory.model_validate(data)

    usage = {
        "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
        "completion_tokens": response.usage.completion_tokens if response.usage else 0,
    }

    logger.info("Generated story '%s' with %d segments", story.title, len(story.segments))
    return story, usage
