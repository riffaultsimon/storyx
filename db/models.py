import json
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    TypeDecorator,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class JSONField(TypeDecorator):
    """Store JSON as text, compatible with both SQLite and PostgreSQL."""
    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            return json.dumps(value, ensure_ascii=False)
        return None

    def process_result_value(self, value, dialect):
        if value is not None:
            return json.loads(value)
        return None


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    is_admin = Column(Boolean, default=False, nullable=False, server_default="0")
    credit_balance = Column(Integer, default=0, nullable=False, server_default="0")

    stories = relationship("Story", back_populates="user", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")


class Story(Base):
    __tablename__ = "stories"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    title = Column(String(300), nullable=False)
    topic = Column(String(200))
    setting = Column(String(200))
    mood = Column(String(50))
    age_range = Column(String(10))
    story_length = Column(String(20))
    language = Column(String(10), default="en", nullable=False, server_default="en")
    story_json = Column(JSONField)
    summary = Column(Text)
    cover_image_path = Column(String(500))
    audio_path = Column(String(500))
    duration_seconds = Column(Float)
    status = Column(String(20), default="generating", nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    bgm_path = Column(String(500), nullable=True)

    cost_story_generation = Column(Float, default=0.0)
    cost_cover_image = Column(Float, default=0.0)
    cost_tts = Column(Float, default=0.0)
    cost_bgm = Column(Float, default=0.0)
    cost_total = Column(Float, default=0.0)
    segment_count = Column(Integer, default=0)
    total_tts_chars = Column(Integer, default=0)
    user_recordings = Column(JSONField, nullable=True)

    user = relationship("User", back_populates="stories")
    transactions = relationship("Transaction", back_populates="story")


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    type = Column(String(20), nullable=False)  # "purchase" or "usage"
    credits = Column(Integer, nullable=False)  # positive for purchase, negative for usage
    amount_usd = Column(Float, default=0.0)
    stripe_session_id = Column(String(255), nullable=True)
    stripe_payment_intent = Column(String(255), nullable=True)
    story_id = Column(String(36), ForeignKey("stories.id"), nullable=True)
    description = Column(String(500))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="transactions")
    story = relationship("Story", back_populates="transactions")


class LoginAttempt(Base):
    __tablename__ = "login_attempts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), nullable=False, index=True)
    attempted_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    success = Column(Boolean, nullable=False)


class AppSettings(Base):
    """Singleton settings table — always exactly one row with id='default'."""
    __tablename__ = "app_settings"

    id = Column(String(36), primary_key=True, default="default")
    image_provider = Column(String(50), default="dalle3", nullable=False, server_default="dalle3")
    bgm_enabled = Column(Boolean, default=False, nullable=False, server_default="0")
    bgm_provider = Column(String(50), default="none", nullable=False, server_default="none")
    story_model = Column(String(100), default="gpt-4o", nullable=False, server_default="gpt-4o")
    tts_model = Column(String(100), default="gpt-4o-mini-tts", nullable=False, server_default="gpt-4o-mini-tts")
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
