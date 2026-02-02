import streamlit as st

from db.session import SessionLocal
from auth.service import login, register
from i18n import t, LANGUAGES


def show_login_page():
    # Language selector on login page too
    lang_codes = list(LANGUAGES.keys())
    current = st.session_state.get("lang", "en")
    idx = lang_codes.index(current) if current in lang_codes else 0
    selected = st.selectbox(
        "🌐",
        lang_codes,
        index=idx,
        format_func=lambda c: LANGUAGES[c],
        label_visibility="collapsed",
    )
    if selected != current:
        st.session_state["lang"] = selected
        st.rerun()

    st.markdown(
        '<div class="main-header">'
        f"<h1>{t('login.title')}</h1>"
        f"<p>{t('login.subtitle')}</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    tab_login, tab_register = st.tabs([t("login.tab_login"), t("login.tab_register")])

    with tab_login:
        with st.form("login_form"):
            email = st.text_input(t("login.email"))
            password = st.text_input(t("login.password"), type="password")
            submitted = st.form_submit_button(t("login.btn_login"))

            if submitted:
                if not email or not password:
                    st.error(t("login.fill_all"))
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
                        st.error(t("login.invalid"))
                finally:
                    db.close()

    with tab_register:
        with st.form("register_form"):
            reg_email = st.text_input(t("login.email"), key="reg_email")
            reg_username = st.text_input(t("login.username"), key="reg_username")
            reg_password = st.text_input(t("login.password"), type="password", key="reg_password")
            reg_confirm = st.text_input(t("login.confirm_password"), type="password", key="reg_confirm")
            accept_terms = st.checkbox(t("login.accept_terms"), key="accept_terms")
            reg_submitted = st.form_submit_button(t("login.btn_register"))

            if reg_submitted:
                if not reg_email or not reg_username or not reg_password:
                    st.error(t("login.fill_all"))
                    return

                if not accept_terms:
                    st.error(t("login.terms_required"))
                    return

                if reg_password != reg_confirm:
                    st.error(t("login.pw_mismatch"))
                    return

                if len(reg_password) < 6:
                    st.error(t("login.pw_too_short"))
                    return

                db = SessionLocal()
                try:
                    user = register(db, reg_email, reg_username, reg_password)
                    if user:
                        st.success(t("login.register_ok"))
                    else:
                        st.error(t("login.already_taken"))
                finally:
                    db.close()
