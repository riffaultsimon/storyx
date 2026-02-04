"""Credit pack definitions and API cost constants."""

CREDIT_PACKS = [
    {
        "credits": 5,
        "price_eur": 4.99,
        "per_credit": 1.00,
        "label": "5 Credits",
        "config_key": "STRIPE_PRICE_ID_5",
    },
    {
        "credits": 15,
        "price_eur": 12.99,
        "per_credit": 0.87,
        "label": "15 Credits",
        "config_key": "STRIPE_PRICE_ID_15",
    },
    {
        "credits": 50,
        "price_eur": 34.99,
        "per_credit": 0.70,
        "label": "50 Credits",
        "config_key": "STRIPE_PRICE_ID_50",
    },
]

FREE_CREDITS_ON_REGISTER = 2

# Estimated API costs per story component

# LLM pricing per 1K tokens: (input, output)
LLM_PRICING = {
    "gpt-4o":       (0.0025, 0.01),
    "gpt-4o-mini":  (0.00015, 0.0006),
    "gpt-4.1":      (0.002, 0.008),
    "gpt-4.1-mini": (0.0004, 0.0016),
}

# Image generation per image
COVER_PRICING = {
    "dalle3":  0.04,
    "imagen3": 0.03,
}

# TTS pricing per 1M characters
TTS_PRICING = {
    "gpt-4o-mini-tts": 15.0,
    "tts-1":           15.0,
    "tts-1-hd":        30.0,
}

# BGM pricing per generation
COST_LYRIA2_PER_GENERATION = 0.05

# Backwards-compatible defaults
COST_GPT4O_PER_1K_INPUT = LLM_PRICING["gpt-4o"][0]
COST_GPT4O_PER_1K_OUTPUT = LLM_PRICING["gpt-4o"][1]
COST_DALLE3_PER_IMAGE = COVER_PRICING["dalle3"]
COST_IMAGEN3_PER_IMAGE = COVER_PRICING["imagen3"]
COST_TTS_PER_1M_CHARS = TTS_PRICING["gpt-4o-mini-tts"]
