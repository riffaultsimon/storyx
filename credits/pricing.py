"""Credit pack definitions and API cost constants."""

CREDIT_PACKS = [
    {
        "credits": 5,
        "price_usd": 4.99,
        "per_credit": 1.00,
        "label": "5 Credits",
        "config_key": "STRIPE_PRICE_ID_5",
    },
    {
        "credits": 15,
        "price_usd": 12.99,
        "per_credit": 0.87,
        "label": "15 Credits",
        "config_key": "STRIPE_PRICE_ID_15",
    },
    {
        "credits": 50,
        "price_usd": 34.99,
        "per_credit": 0.70,
        "label": "50 Credits",
        "config_key": "STRIPE_PRICE_ID_50",
    },
]

FREE_CREDITS_ON_REGISTER = 2

# Estimated API costs per story component
COST_GPT4O_PER_1K_INPUT = 0.0025
COST_GPT4O_PER_1K_OUTPUT = 0.01
COST_DALLE3_PER_IMAGE = 0.04
COST_TTS_PER_1M_CHARS = 15.0  # $15 per 1M characters for gpt-4o-mini-tts
