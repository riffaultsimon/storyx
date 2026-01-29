"""Idempotent SQLite ALTER TABLE migrations for StoryX."""

import logging
from sqlalchemy import inspect, text
from db.session import engine

logger = logging.getLogger(__name__)


def _column_exists(inspector, table: str, column: str) -> bool:
    columns = [c["name"] for c in inspector.get_columns(table)]
    return column in columns


def _table_exists(inspector, table: str) -> bool:
    return table in inspector.get_table_names()


def run_migrations():
    """Run all idempotent migrations."""
    inspector = inspect(engine)

    with engine.begin() as conn:
        # --- User table additions ---
        if _table_exists(inspector, "users"):
            if not _column_exists(inspector, "users", "is_admin"):
                conn.execute(text(
                    "ALTER TABLE users ADD COLUMN is_admin BOOLEAN NOT NULL DEFAULT 0"
                ))
                logger.info("Added users.is_admin column")

            if not _column_exists(inspector, "users", "credit_balance"):
                conn.execute(text(
                    "ALTER TABLE users ADD COLUMN credit_balance INTEGER NOT NULL DEFAULT 0"
                ))
                logger.info("Added users.credit_balance column")

        # --- Story table additions ---
        if _table_exists(inspector, "stories"):
            story_columns = {
                "cost_story_generation": "FLOAT DEFAULT 0.0",
                "cost_cover_image": "FLOAT DEFAULT 0.0",
                "cost_tts": "FLOAT DEFAULT 0.0",
                "cost_total": "FLOAT DEFAULT 0.0",
                "segment_count": "INTEGER DEFAULT 0",
                "total_tts_chars": "INTEGER DEFAULT 0",
            }
            for col_name, col_type in story_columns.items():
                if not _column_exists(inspector, "stories", col_name):
                    conn.execute(text(
                        f"ALTER TABLE stories ADD COLUMN {col_name} {col_type}"
                    ))
                    logger.info("Added stories.%s column", col_name)

        # --- Transactions table ---
        if not _table_exists(inspector, "transactions"):
            conn.execute(text("""
                CREATE TABLE transactions (
                    id VARCHAR(36) PRIMARY KEY,
                    user_id VARCHAR(36) NOT NULL REFERENCES users(id),
                    type VARCHAR(20) NOT NULL,
                    credits INTEGER NOT NULL,
                    amount_usd FLOAT DEFAULT 0.0,
                    stripe_session_id VARCHAR(255),
                    stripe_payment_intent VARCHAR(255),
                    story_id VARCHAR(36) REFERENCES stories(id),
                    description VARCHAR(500),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """))
            logger.info("Created transactions table")

    logger.info("Migrations complete")
