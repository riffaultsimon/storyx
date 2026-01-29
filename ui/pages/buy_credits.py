import streamlit as st

from credits.pricing import CREDIT_PACKS
from credits.service import check_balance
from credits.stripe_checkout import create_checkout_session
from config import STRIPE_SECRET_KEY
from db.session import SessionLocal


def show_buy_credits_page():
    st.markdown("## Buy Credits")

    db = SessionLocal()
    try:
        balance = check_balance(db, st.session_state["user_id"])
    finally:
        db.close()

    st.markdown(f"**Current balance:** {balance} credits")
    st.markdown("Each credit lets you generate one complete story with cover art and audio.")
    st.divider()

    if not STRIPE_SECRET_KEY:
        st.warning("Stripe is not configured. Please set STRIPE_SECRET_KEY in your environment.")
        return

    cols = st.columns(len(CREDIT_PACKS))

    for i, pack in enumerate(CREDIT_PACKS):
        with cols[i]:
            st.markdown(
                f"### {pack['label']}\n"
                f"**${pack['price_usd']:.2f}**\n\n"
                f"${pack['per_credit']:.2f} per credit"
            )
            if st.button(f"Buy {pack['credits']} Credits", key=f"buy_{pack['credits']}"):
                with st.spinner("Redirecting to checkout..."):
                    url = create_checkout_session(
                        st.session_state["user_id"],
                        pack["credits"],
                    )
                    if url:
                        st.markdown(
                            f'<meta http-equiv="refresh" content="0;url={url}">',
                            unsafe_allow_html=True,
                        )
                        st.info("Redirecting to Stripe checkout...")
                    else:
                        st.error("Failed to create checkout session. Check Stripe configuration.")
