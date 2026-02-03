import math
from datetime import datetime, timedelta, timezone

import bcrypt
from sqlalchemy.orm import Session

from db.models import LoginAttempt, User

RATE_LIMIT_WINDOW_MINUTES = 15
RATE_LIMIT_MAX_FAILURES = 5


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def record_login_attempt(db: Session, email: str, success: bool):
    attempt = LoginAttempt(email=email, success=success)
    db.add(attempt)
    db.commit()


def is_rate_limited(db: Session, email: str) -> bool:
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=RATE_LIMIT_WINDOW_MINUTES)
    count = (
        db.query(LoginAttempt)
        .filter(
            LoginAttempt.email == email,
            LoginAttempt.success == False,
            LoginAttempt.attempted_at >= cutoff,
        )
        .count()
    )
    return count >= RATE_LIMIT_MAX_FAILURES


def rate_limit_minutes_remaining(db: Session, email: str) -> int:
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=RATE_LIMIT_WINDOW_MINUTES)
    oldest = (
        db.query(LoginAttempt)
        .filter(
            LoginAttempt.email == email,
            LoginAttempt.success == False,
            LoginAttempt.attempted_at >= cutoff,
        )
        .order_by(LoginAttempt.attempted_at.asc())
        .first()
    )
    if not oldest:
        return 0
    expires = oldest.attempted_at + timedelta(minutes=RATE_LIMIT_WINDOW_MINUTES)
    remaining = (expires - datetime.now(timezone.utc)).total_seconds() / 60
    return max(1, math.ceil(remaining))


def clear_login_attempts(db: Session, email: str):
    db.query(LoginAttempt).filter(
        LoginAttempt.email == email,
        LoginAttempt.success == False,
    ).delete()
    db.commit()


def register(db: Session, email: str, username: str, password: str) -> User | None:
    existing = db.query(User).filter(
        (User.email == email) | (User.username == username)
    ).first()
    if existing:
        return None

    user = User(
        email=email,
        username=username,
        password_hash=hash_password(password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    from credits.service import grant_free_credits
    from credits.pricing import FREE_CREDITS_ON_REGISTER
    grant_free_credits(db, user.id, FREE_CREDITS_ON_REGISTER)
    db.refresh(user)

    return user


def login(db: Session, email: str, password: str) -> User | None:
    user = db.query(User).filter(User.email == email).first()
    if user and verify_password(password, user.password_hash):
        return user
    return None


def get_user_by_id(db: Session, user_id) -> User | None:
    return db.query(User).filter(User.id == user_id).first()


def get_or_create_google_user(db: Session, google_id: str, email: str, name: str) -> User:
    """Get existing user by Google ID or email, or create a new one.

    If user exists with same email but no google_id, link the accounts.

    Args:
        db: Database session.
        google_id: Google's unique user ID.
        email: User's email from Google.
        name: User's display name from Google.

    Returns:
        The user object.
    """
    # First check if user exists by google_id
    user = db.query(User).filter(User.google_id == google_id).first()
    if user:
        return user

    # Check if user exists by email (might have registered with password)
    user = db.query(User).filter(User.email == email).first()
    if user:
        # Link the Google account to existing user
        user.google_id = google_id
        db.commit()
        db.refresh(user)
        return user

    # Create new user
    # Generate a username from email or name
    base_username = name.lower().replace(" ", "_") if name else email.split("@")[0]
    username = base_username
    counter = 1

    # Ensure username is unique
    while db.query(User).filter(User.username == username).first():
        username = f"{base_username}_{counter}"
        counter += 1

    user = User(
        email=email,
        username=username,
        password_hash=None,  # No password for OAuth-only users
        google_id=google_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Grant free credits to new users
    from credits.service import grant_free_credits
    from credits.pricing import FREE_CREDITS_ON_REGISTER
    grant_free_credits(db, user.id, FREE_CREDITS_ON_REGISTER)
    db.refresh(user)

    return user
