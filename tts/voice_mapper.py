from story.schema import CharacterProfile

# OpenAI TTS voices mapped by character profile.
# Voices: alloy, ash, ballad, coral, echo, fable, nova, onyx, sage, shimmer
#
# Masculine-leaning:  ash (warm), echo (steady), fable (expressive), onyx (deep)
# Feminine-leaning:   alloy (neutral), coral (warm), nova (bright), shimmer (soft)
# Neutral/versatile:  ballad (gentle), sage (calm)

_VOICE_MAP = {
    # (gender, age_bucket) -> voice
    ("female", "child"):   "shimmer",
    ("female", "teen"):    "nova",
    ("female", "adult"):   "coral",
    ("female", "elder"):   "sage",
    ("male", "child"):     "alloy",
    ("male", "teen"):      "echo",
    ("male", "adult"):     "ash",
    ("male", "elder"):     "onyx",
    ("neutral", "child"):  "shimmer",
    ("neutral", "teen"):   "alloy",
    ("neutral", "adult"):  "ballad",
    ("neutral", "elder"):  "sage",
}

_NARRATOR_VOICE = "fable"

_EMOTION_STYLE = {
    "neutral":   "Speak in a natural, conversational tone with subtle warmth. Vary your pacing slightly to keep the listener engaged — don't be monotone.",
    "happy":     "Speak with genuine joy and a bright, playful energy. Let your voice rise naturally with excitement, as if you're sharing wonderful news with a child. Smile as you speak.",
    "sad":       "Speak softly and slowly, with a tender, bittersweet quality. Let pauses breathe. Your voice should feel heavy with emotion but still gentle, like comforting someone.",
    "excited":   "Speak with bubbling enthusiasm and rising energy! Let your pitch climb with anticipation. Your pace should quicken naturally, like you can barely contain the thrill of what's happening.",
    "scared":    "Speak in a hushed, trembling voice. Let your words come out slightly uneven, with nervous pauses. Your breath should feel short, as if something might jump out at any moment.",
    "angry":     "Speak with intensity and barely contained emotion. Your voice should be firm and punchy, with sharp emphasis on key words. Keep it controlled but let the frustration bleed through.",
    "whisper":   "Speak in a hushed, secretive whisper — as if sharing a secret with the listener. Keep it intimate and conspiratorial, barely above a breath.",
    "gentle":    "Speak in a soft, lullaby-like tone dripping with tenderness and care. Your voice should feel like a warm hug — slow, soothing, and full of love.",
    "surprised": "Speak with wide-eyed astonishment! Let a small gasp escape before the words. Your pitch should jump up with genuine wonder, as if you can't believe what just happened.",
}


def _age_bucket(age: int) -> str:
    if age < 13:
        return "child"
    if age < 18:
        return "teen"
    if age < 60:
        return "adult"
    return "elder"


def pick_voice(character: CharacterProfile) -> str:
    """Select an OpenAI TTS voice based on character gender and age."""
    bucket = _age_bucket(character.age)
    return _VOICE_MAP.get((character.gender, bucket), "alloy")


def build_voice_instruction(character: CharacterProfile, emotion: str) -> str:
    """Build an instruction string for the TTS model."""
    emotion_style = _EMOTION_STYLE.get(emotion, _EMOTION_STYLE["neutral"])
    return (
        f"You are performing the role of {character.name}, "
        f"a {character.age}-year-old {character.gender} character in a children's story. "
        f"{character.description}. "
        f"{emotion_style} "
        f"Bring this character to life — use expressive vocal dynamics, natural breathing pauses, "
        f"and age-appropriate energy. This is a performance, not a reading."
    )


def get_narrator_voice() -> str:
    return _NARRATOR_VOICE


def build_narrator_instruction(emotion: str = "neutral") -> str:
    """Build an instruction for narration segments."""
    emotion_style = _EMOTION_STYLE.get(emotion, _EMOTION_STYLE["neutral"])
    return (
        f"You are a beloved storyteller reading a bedtime story to a child. "
        f"Speak with the warmth and expressiveness of a grandparent who truly loves telling stories. "
        f"{emotion_style} "
        f"Use dramatic pauses for suspense, shift your tone to match the scene, "
        f"and let your voice paint the world of the story. Never sound like you're reading — sound like you're living it."
    )
