import streamlit as st

from db.models import User, Story, Transaction
from db.session import SessionLocal
from auth.service import hash_password, verify_password


def show_account_page():
    st.markdown("## Account Settings")

    user_id = st.session_state["user_id"]
    db = SessionLocal()

    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            st.error("User not found.")
            return

        # Profile info
        st.markdown("### Profile")
        st.markdown(f"**Username:** {user.username}")
        st.markdown(f"**Email:** {user.email}")
        st.markdown(f"**Member since:** {user.created_at.strftime('%B %d, %Y')}")

        # Stats
        story_count = db.query(Story).filter(Story.user_id == user_id).count()
        ready_count = (
            db.query(Story)
            .filter(Story.user_id == user_id, Story.status == "ready")
            .count()
        )
        st.markdown("### Stats")
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Stories", story_count)
        col2.metric("Completed Stories", ready_count)
        col3.metric("Credit Balance", user.credit_balance)

        # Transaction history
        st.markdown("### Transaction History")
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
            st.info("No transactions yet.")

        # Change password
        st.markdown("### Change Password")
        with st.form("change_password"):
            current_pw = st.text_input("Current Password", type="password")
            new_pw = st.text_input("New Password", type="password")
            confirm_pw = st.text_input("Confirm New Password", type="password")
            submitted = st.form_submit_button("Update Password")

            if submitted:
                if not current_pw or not new_pw or not confirm_pw:
                    st.error("Please fill in all fields.")
                elif new_pw != confirm_pw:
                    st.error("New passwords do not match.")
                elif len(new_pw) < 6:
                    st.error("Password must be at least 6 characters.")
                elif not verify_password(current_pw, user.password_hash):
                    st.error("Current password is incorrect.")
                else:
                    user.password_hash = hash_password(new_pw)
                    db.commit()
                    st.success("Password updated successfully.")

    finally:
        db.close()
