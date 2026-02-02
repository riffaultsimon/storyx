import streamlit as st

from db.models import User, Story, Transaction
from db.session import SessionLocal
from auth.service import hash_password, verify_password
from i18n import t


def show_account_page():
    st.markdown(f"## {t('account.header')}")

    user_id = st.session_state["user_id"]
    db = SessionLocal()

    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            st.error(t("account.not_found"))
            return

        # Profile info
        st.markdown(f"### {t('account.profile')}")
        st.markdown(t("account.username", username=user.username))
        st.markdown(t("account.email", email=user.email))
        st.markdown(t("account.member_since", date=user.created_at.strftime('%B %d, %Y')))

        # Stats
        story_count = db.query(Story).filter(Story.user_id == user_id).count()
        ready_count = (
            db.query(Story)
            .filter(Story.user_id == user_id, Story.status == "ready")
            .count()
        )
        st.markdown(f"### {t('account.stats')}")
        col1, col2, col3 = st.columns(3)
        col1.metric(t("account.total_stories"), story_count)
        col2.metric(t("account.completed"), ready_count)
        col3.metric(t("account.credit_balance"), user.credit_balance)

        # Transaction history
        st.markdown(f"### {t('account.transactions')}")
        transactions = (
            db.query(Transaction)
            .filter(Transaction.user_id == user_id)
            .order_by(Transaction.created_at.desc())
            .limit(50)
            .all()
        )
        if transactions:
            for txn in transactions:
                sign = "+" if txn.credits > 0 else ""
                amount_str = f" (${txn.amount_usd:.2f})" if txn.amount_usd else ""
                st.markdown(
                    f"- **{sign}{txn.credits} credits** — {txn.description}{amount_str} "
                    f"*({txn.created_at.strftime('%Y-%m-%d %H:%M')})*"
                )
        else:
            st.info(t("account.no_transactions"))

        # Change password
        st.markdown(f"### {t('account.change_pw')}")
        with st.form("change_password"):
            current_pw = st.text_input(t("account.current_pw"), type="password")
            new_pw = st.text_input(t("account.new_pw"), type="password")
            confirm_pw = st.text_input(t("account.confirm_pw"), type="password")
            submitted = st.form_submit_button(t("account.btn_update_pw"))

            if submitted:
                if not current_pw or not new_pw or not confirm_pw:
                    st.error(t("account.fill_all"))
                elif new_pw != confirm_pw:
                    st.error(t("account.pw_mismatch"))
                elif len(new_pw) < 8:
                    st.error(t("account.pw_too_short"))
                elif not verify_password(current_pw, user.password_hash):
                    st.error(t("account.pw_incorrect"))
                else:
                    user.password_hash = hash_password(new_pw)
                    db.commit()
                    st.success(t("account.pw_updated"))

    finally:
        db.close()
