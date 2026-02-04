import streamlit as st

from credits.pricing import CREDIT_PACKS
from credits.service import check_balance
from credits.stripe_checkout import create_checkout_session
from config import STRIPE_SECRET_KEY
from db.session import SessionLocal
from i18n import t
from ui.loader import storyx_loader


def show_buy_credits_page():
    st.markdown(f"## {t('credits.header')}")

    db = SessionLocal()
    try:
        balance = check_balance(db, st.session_state["user_id"])
    finally:
        db.close()

    st.markdown(t("credits.balance", balance=balance))
    st.markdown(t("credits.description"))

    # Stripe logo
    st.markdown(
        '<div style="margin: 1rem 0;">'
        '<svg viewBox="0 0 60 25" xmlns="http://www.w3.org/2000/svg" width="80" height="33">'
        '<path fill="#635bff" d="M59.64 14.28h-8.06c.19 1.93 1.6 2.55 3.2 2.55 1.64 0 2.96-.37 4.05-.95v3.32a8.33 8.33 0 0 1-4.56 1.1c-4.01 0-6.83-2.5-6.83-7.48 0-4.19 2.39-7.52 6.3-7.52 3.92 0 5.96 3.28 5.96 7.5 0 .4-.02 1.04-.06 1.48zm-3.67-3.32c0-1.47-.66-2.63-2.1-2.63-1.38 0-2.19 1.1-2.32 2.63zM41.48 20.51c-1.65 0-2.74-.84-3.03-1.6l-.04 1.35h-3.94V.64l4.03-.68v5.14l.04.05c.7-.8 1.81-1.45 3.3-1.45 3.3 0 5.16 2.88 5.16 6.81 0 4.72-2.18 7.5-5.52 7.5v2.5zm-.96-11.21c-.95 0-1.54.39-1.9.88v4.84c.36.49.95.9 1.9.9 1.5 0 2.4-1.4 2.4-3.32 0-1.91-.9-3.3-2.4-3.3zM28.5 4.12c1.38 0 2.5-1.1 2.5-2.48a2.5 2.5 0 0 0-2.5-2.5c-1.4 0-2.5 1.13-2.5 2.5s1.1 2.48 2.5 2.48zm2 16.13h-4.02V5.88h4.02zm-8.95-5.59c0 2.27-1.87 4.36-5.16 4.36-1.77 0-3.51-.55-4.88-1.63l1.32-2.86c1.01.68 2.32 1.26 3.63 1.26.88 0 1.37-.3 1.37-.83 0-1.67-6.08-.82-6.08-5.27 0-2.3 1.87-4.35 5-4.35 1.54 0 3.06.4 4.25 1.22L14.8 8.9c-.9-.54-1.95-.87-2.94-.87-.78 0-1.2.3-1.2.8 0 1.56 6.09.68 6.09 5.23zM.45 5.88l4-.68v11.7c0 3.09 1.32 4.64 4.43 4.64.88 0 1.79-.14 2.55-.43v-3.24c-.52.14-1.1.21-1.68.21-1.1 0-1.61-.55-1.61-1.74V9.4h3.29V5.88H8.14V1.44L4.11 2.12v3.76z"/>'
        '</svg>'
        '</div>',
        unsafe_allow_html=True,
    )
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
