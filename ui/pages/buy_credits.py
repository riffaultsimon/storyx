import streamlit as st

from credits.pricing import CREDIT_PACKS
from credits.service import check_balance
from credits.stripe_checkout import create_checkout_session
from config import STRIPE_SECRET_KEY
from db.session import SessionLocal
from i18n import t
from ui.loader import storyx_loader


_STRIPE_BADGE = (
    '<div style="display:flex;align-items:center;gap:8px;margin:0.75rem 0;">'
    '<svg viewBox="0 0 60 25" xmlns="http://www.w3.org/2000/svg" '
    'style="height:25px;width:60px;">'
    '<path fill="#635BFF" d="M5 10.2c0-.7.6-1 1.5-1 1.3 0 3 .4 4.3 1.1V7'
    'c-1.5-.6-2.9-.8-4.3-.8C3.6 6.2 1.5 7.8 1.5 10.4c0 4 5.5 3.4 5.5 5.1'
    ' 0 .9-.7 1.1-1.8 1.1-1.5 0-3.5-.6-5-1.5v3.4c1.7.7 3.4 1.1 5 1.1'
    ' 3 0 5.1-1.5 5.1-4.1C10.3 11.3 5 12 5 10.2zM16 3.8l-3.4.7v3.3h3.4'
    'V3.8zm0 4.4h-3.4v11h3.4v-11zM22 7.2l-.2-1h-3v13h3.4v-8.8c.8-1 '
    '2.2-1.8 3.6-.8V6.2c-1.5-.6-2.9.2-3.8 1zm9-1c-1.2 0-2 .6-2.4 1'
    'l-.2-.8h-3v13l3.4-.7v-3.2c.5.3 1.2.8 2.3.8 2.3 0 4.5-1.9 4.5-6'
    ' 0-3.8-2.2-6.1-4.6-6.1zm-.8 9.4c-.8 0-1.2-.3-1.6-.6v-5c.4-.4.8'
    '-.7 1.6-.7 1.2 0 2 1.4 2 3.2 0 1.8-.8 3.1-2 3.1zm11.5-1.2c0 2.7'
    ' 1.3 4.2 3.8 4.2 1.1 0 1.9-.3 2.6-.6v-2.7c-.6.3-1.3.5-2.1.5-1.1'
    ' 0-1.8-.5-1.8-1.8v-5h1.8V6.2H44v-3l-3.4.7v2.3h-2.3V8h2.3v6.4z'
    'M54.5 6.2c-1.8 0-3 .8-3.7 1.5l-.2-1.2h-3v13.1l3.4-.7v-3.1c.5.4'
    ' 1.2.8 2.4.8 2.4 0 4.6-1.9 4.6-6.1-.1-3.8-2.3-6.3-4.6-6.3h1.1'
    'zm-1 9.4c-.8 0-1.2-.3-1.5-.6v-5c.4-.4.8-.7 1.5-.7 1.2 0 2 1.4 2'
    ' 3.2.1 1.8-.7 3.1-2 3.1z"/>'
    '</svg>'
    '<span style="color:#636E72;font-size:0.8rem;">Secure payments</span>'
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
