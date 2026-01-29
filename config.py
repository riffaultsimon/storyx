import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///storyx.db")
STORAGE_DIR = os.getenv("STORAGE_DIR", "./media")

# Story generation
STORY_MODEL = "gpt-4o"
COVER_MODEL = "dall-e-3"
COVER_SIZE = "1024x1024"
COVER_STYLE = "vivid"

# TTS (OpenAI)
TTS_MODEL = "gpt-4o-mini-tts"
TTS_RESPONSE_FORMAT = "mp3"

# Audio
DEFAULT_PAUSE_MS = 400
SEGMENT_PAUSE_MS = 200

# Stripe
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY", "")
STRIPE_PRICE_ID_5 = os.getenv("STRIPE_PRICE_ID_5", "")
STRIPE_PRICE_ID_15 = os.getenv("STRIPE_PRICE_ID_15", "")
STRIPE_PRICE_ID_50 = os.getenv("STRIPE_PRICE_ID_50", "")
APP_BASE_URL = os.getenv("APP_BASE_URL", "http://localhost:8501")

# Emotions supported
EMOTIONS = [
    "neutral", "happy", "sad", "excited", "scared",
    "angry", "whisper", "gentle", "surprised",
]

# Age ranges
AGE_RANGES = ["3-5", "6-8", "9-12"]

# Story lengths
STORY_LENGTHS = ["short", "medium", "long"]

# Moods
MOODS = ["adventurous", "funny", "heartwarming", "mysterious", "educational", "calming"]
