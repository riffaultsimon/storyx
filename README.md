# StoryX

AI-powered children's story platform that generates illustrated, voiced stories tailored to age ranges and moods. Built with Streamlit, OpenAI (GPT-4o, DALL-E 3, TTS), and SQLite.

## Features

- **Story Generation** — GPT-4o creates structured stories with characters, dialog, emotions, and morals
- **Cover Art** — DALL-E 3 generates children's book-style cover illustrations
- **Text-to-Speech** — Multi-voice, emotion-aware audio narration using gpt-4o-mini-tts
- **Audio Assembly** — Segments are stitched into a single MP3 with natural pauses
- **Credit System** — Users purchase credits to generate stories (2 free on registration)
- **Stripe Payments** — Buy credit packs ($4.99/5cr, $12.99/15cr, $34.99/50cr)
- **Admin Dashboard** — User management, revenue tracking, API cost analytics
- **Background Processing** — TTS runs asynchronously so the UI stays responsive

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment

Copy `.env.example` to `.env` and fill in your keys:

```bash
cp .env.example .env
```

Required:
- `OPENAI_API_KEY` — Your OpenAI API key

Optional (for credit purchases):
- `STRIPE_SECRET_KEY` / `STRIPE_PUBLISHABLE_KEY` — Stripe API keys
- `STRIPE_PRICE_ID_5` / `STRIPE_PRICE_ID_15` / `STRIPE_PRICE_ID_50` — Stripe Price IDs for each credit pack
- `APP_BASE_URL` — Your app's public URL (default: `http://localhost:8501`)

### 3. Run

```bash
streamlit run app.py
```

### 4. Create an admin user

Register a normal account, then promote it via the database:

```bash
sqlite3 storyx.db "UPDATE users SET is_admin = 1 WHERE email = 'your@email.com';"
```

Log out and back in to see the Admin panel.

## Project Structure

```
storyx/
├── app.py                  # Main Streamlit entry point
├── config.py               # Configuration & constants
├── requirements.txt
├── .env.example
├── db/
│   ├── models.py           # SQLAlchemy models (User, Story, Transaction)
│   ├── session.py           # DB engine & session
│   └── migrate.py           # Idempotent SQLite migrations
├── auth/
│   └── service.py           # Registration, login, password hashing
├── credits/
│   ├── pricing.py           # Credit pack definitions & API cost constants
│   ├── service.py           # Balance check, deduct, add credits
│   ├── stripe_checkout.py   # Stripe Checkout Session flow
│   └── cost_tracker.py      # Per-story API cost estimation
├── story/
│   ├── generator.py         # GPT-4o story generation
│   ├── cover.py             # DALL-E 3 cover image generation
│   └── schema.py            # Pydantic models
├── tts/
│   ├── engine.py            # OpenAI TTS synthesis
│   ├── pipeline.py          # Multi-segment TTS pipeline
│   └── voice_mapper.py      # Voice & emotion mapping
├── audio/
│   └── assembler.py         # MP3 assembly with pauses
├── storage/
│   └── file_store.py        # File storage helpers
├── workers/
│   └── story_worker.py      # Background TTS worker
└── ui/
    ├── theme.py             # Custom CSS
    └── pages/
        ├── login.py
        ├── create_story.py
        ├── library.py
        ├── account.py
        ├── buy_credits.py
        └── admin.py
```

## Credit System

| Pack | Price | Per Credit |
|------|-------|-----------|
| 5 credits | $4.99 | $1.00 |
| 15 credits | $12.99 | $0.87 |
| 50 credits | $34.99 | $0.70 |

New users receive 2 free credits on registration. Each story generation costs 1 credit.

## Tech Stack

- **Frontend**: Streamlit
- **AI**: OpenAI GPT-4o, DALL-E 3, gpt-4o-mini-tts
- **Database**: SQLAlchemy + SQLite (PostgreSQL optional)
- **Payments**: Stripe Checkout
- **Audio**: pydub
- **Auth**: bcrypt
