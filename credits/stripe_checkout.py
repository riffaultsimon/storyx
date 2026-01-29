"""Stripe Checkout Session creation and fulfillment."""

import logging

import stripe

from config import (
    APP_BASE_URL,
    STRIPE_PRICE_ID_5,
    STRIPE_PRICE_ID_15,
    STRIPE_PRICE_ID_50,
    STRIPE_SECRET_KEY,
)
from credits.pricing import CREDIT_PACKS

logger = logging.getLogger(__name__)

stripe.api_key = STRIPE_SECRET_KEY

PRICE_ID_MAP = {
    5: STRIPE_PRICE_ID_5,
    15: STRIPE_PRICE_ID_15,
    50: STRIPE_PRICE_ID_50,
}


def _get_pack_by_credits(credits: int) -> dict | None:
    for pack in CREDIT_PACKS:
        if pack["credits"] == credits:
            return pack
    return None


def create_checkout_session(user_id: str, credit_count: int) -> str | None:
    """Create a Stripe Checkout Session and return the URL.

    Returns None if Stripe keys are not configured.
    """
    price_id = PRICE_ID_MAP.get(credit_count)
    if not price_id or not STRIPE_SECRET_KEY:
        return None

    pack = _get_pack_by_credits(credit_count)
    if not pack:
        return None

    session = stripe.checkout.Session.create(
        mode="payment",
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=f"{APP_BASE_URL}/?stripe_session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{APP_BASE_URL}/?stripe_cancelled=1",
        metadata={
            "user_id": user_id,
            "credits": str(credit_count),
        },
    )
    return session.url


def verify_and_fulfill(db, session_id: str) -> dict | None:
    """Retrieve a Checkout Session and fulfill if paid.

    Returns dict with session info if paid & not already fulfilled, else None.
    """
    from db.models import Transaction

    # Idempotency: check if already fulfilled
    existing = (
        db.query(Transaction)
        .filter(Transaction.stripe_session_id == session_id)
        .first()
    )
    if existing:
        logger.info("Session %s already fulfilled", session_id)
        return None

    try:
        session = stripe.checkout.Session.retrieve(session_id)
    except Exception as e:
        logger.error("Failed to retrieve Stripe session %s: %s", session_id, e)
        return None

    if session.payment_status != "paid":
        logger.warning("Session %s not paid (status=%s)", session_id, session.payment_status)
        return None

    user_id = session.metadata.get("user_id")
    credits = int(session.metadata.get("credits", 0))
    payment_intent = session.payment_intent

    if not user_id or credits <= 0:
        logger.error("Invalid metadata in session %s", session_id)
        return None

    pack = _get_pack_by_credits(credits)
    amount_usd = pack["price_usd"] if pack else 0.0

    from credits.service import add_credits

    add_credits(
        db,
        user_id=user_id,
        credits=credits,
        amount_usd=amount_usd,
        stripe_session_id=session_id,
        stripe_payment_intent=payment_intent,
        description=f"Purchased {credits} credits",
    )

    return {
        "user_id": user_id,
        "credits": credits,
        "amount_usd": amount_usd,
    }
