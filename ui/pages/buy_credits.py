import streamlit as st

from credits.pricing import CREDIT_PACKS
from credits.service import check_balance
from credits.stripe_checkout import create_checkout_session
from config import STRIPE_SECRET_KEY
from db.session import SessionLocal
from i18n import t
from ui.loader import storyx_loader


_STRIPE_BADGE = (
    '<div style="display:inline-flex;align-items:center;gap:6px;'
    'padding:6px 14px;border-radius:6px;border:1px solid #e3e3e8;'
    'background:white;margin:0.75rem 0;">'
    '<span style="font-weight:700;color:#635BFF;font-size:1.2rem;'
    'font-family:system-ui,sans-serif;letter-spacing:-0.5px;">stripe</span>'
    '<span style="color:#636E72;font-size:0.8rem;border-left:1px solid #e3e3e8;'
    'padding-left:6px;">Secure payments</span>'
    '</div>'
)


def show_buy_credits_page():
    st.markdown(f"## {t('credits.header')}")

    db = SessionLocal()
    try:
        balance = check_balance(db, st.session_state["user_id"])
    finally:
        db.close()

    st.markdown(t("credits.balance", balance=balance))
    st.markdown(t("credits.description"))
    st.markdown(_STRIPE_BADGE, unsafe_allow_html=True)
    st.divider()

    if not STRIPE_SECRET_KEY:
        st.warning(t("credits.stripe_missing"))
        return

    cols = st.columns(len(CREDIT_PACKS))

    for i, pack in enumerate(CREDIT_PACKS):
        with cols[i]:
            per_credit = f"€{pack['per_credit']:.2f}"
            st.markdown(
                f"### {pack['label']}\n"
                f"**€{pack['price_eur']:.2f}**\n\n"
                f"{t('credits.per_credit', price=per_credit)}"
            )
            if st.button(t("credits.btn_buy", credits=pack['credits']), key=f"buy_{pack['credits']}"):
                with storyx_loader(t("credits.redirecting")):
                    url = create_checkout_session(
                        st.session_state["user_id"],
                        pack["credits"],
                    )
                    if url:
                        st.markdown(
                            f'<meta http-equiv="refresh" content="0;url={url}">',
                            unsafe_allow_html=True,
                        )
                        st.info(t("credits.redirect_info"))
                    else:
                        st.error(t("credits.checkout_failed"))
