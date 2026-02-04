"""Credit balance operations."""

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from db.models import User, Transaction


def check_balance(db: Session, user_id: str) -> int:
    user = db.query(User).filter(User.id == user_id).first()
    return user.credit_balance if user else 0


def deduct_credit(db: Session, user_id: str, story_id: str | None = None) -> Transaction | None:
    """Deduct 1 credit for story generation. Returns the Transaction, or None if insufficient balance."""
    user = db.query(User).filter(User.id == user_id).with_for_update().first()
    if not user or user.credit_balance < 1:
        return None

    user.credit_balance -= 1

    txn = Transaction(
        id=str(uuid.uuid4()),
        user_id=user_id,
        type="usage",
        credits=-1,
        story_id=story_id,
        description="Story generation",
    )
    db.add(txn)
    db.commit()
    db.refresh(txn)
    return txn


def add_credits(
    db: Session,
    user_id: str,
    credits: int,
    amount_eur: float = 0.0,
    stripe_session_id: str | None = None,
    stripe_payment_intent: str | None = None,
    description: str = "",
) -> Transaction:
    """Add credits to a user's balance and record the transaction."""
    user = db.query(User).filter(User.id == user_id).with_for_update().first()
    user.credit_balance += credits

    txn = Transaction(
        id=str(uuid.uuid4()),
        user_id=user_id,
        type="purchase",
        credits=credits,
        amount_usd=amount_eur,  # DB field stores EUR amount
        stripe_session_id=stripe_session_id,
        stripe_payment_intent=stripe_payment_intent,
        description=description,
    )
    db.add(txn)
    db.commit()
    db.refresh(txn)
    return txn


def grant_free_credits(db: Session, user_id: str, credits: int):
    """Grant free credits (e.g. on registration)."""
    add_credits(
        db,
        user_id,
        credits=credits,
        description=f"Welcome bonus: {credits} free credits",
    )
