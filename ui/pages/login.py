import streamlit as st

from db.session import SessionLocal
from auth.service import login, register


def show_login_page():
    st.markdown(
        '<div class="main-header">'
        "<h1>StoryX</h1>"
        "<p>Magical stories for little dreamers</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    tab_login, tab_register = st.tabs(["Login", "Register"])

    with tab_login:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")

            if submitted:
                if not email or not password:
                    st.error("Please fill in all fields.")
                    return

                db = SessionLocal()
                try:
                    user = login(db, email, password)
                    if user:
                        st.session_state["user_id"] = str(user.id)
                        st.session_state["username"] = user.username
                        st.session_state["is_admin"] = bool(user.is_admin)
                        st.session_state["logged_in"] = True
                        st.rerun()
                    else:
                        st.error("Invalid email or password.")
                finally:
                    db.close()

    with tab_register:
        with st.form("register_form"):
            reg_email = st.text_input("Email", key="reg_email")
            reg_username = st.text_input("Username", key="reg_username")
            reg_password = st.text_input("Password", type="password", key="reg_password")
            reg_confirm = st.text_input("Confirm Password", type="password", key="reg_confirm")
            reg_submitted = st.form_submit_button("Create Account")

            if reg_submitted:
                if not reg_email or not reg_username or not reg_password:
                    st.error("Please fill in all fields.")
                    return

                if reg_password != reg_confirm:
                    st.error("Passwords do not match.")
                    return

                if len(reg_password) < 6:
                    st.error("Password must be at least 6 characters.")
                    return

                db = SessionLocal()
                try:
                    user = register(db, reg_email, reg_username, reg_password)
                    if user:
                        st.success("Account created! You can now log in.")
                    else:
                        st.error("Email or username already taken.")
                finally:
                    db.close()
