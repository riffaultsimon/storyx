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
