import streamlit as st

from db.session import SessionLocal
from auth.service import (
    login,
    register,
    is_rate_limited,
    rate_limit_minutes_remaining,
    record_login_attempt,
    clear_login_attempts,
)
from auth.validation import is_valid_email, password_strength
from auth.google_oauth import is_google_oauth_configured, generate_auth_url
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

    # Google Sign-In button
    if is_google_oauth_configured():
        if st.button(t("login.google_signin"), type="primary", use_container_width=True):
            auth_url, state = generate_auth_url()
            st.session_state["oauth_state"] = state
            st.markdown(
                f'<meta http-equiv="refresh" content="0;url={auth_url}">',
                unsafe_allow_html=True,
            )
            st.info(t("login.google_redirect"))
            st.stop()

        st.markdown(
            '<div style="text-align: center; margin: 1rem 0; color: #888;">— ' +
            t("login.or_email") + ' —</div>',
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
                    if is_rate_limited(db, email):
                        minutes = rate_limit_minutes_remaining(db, email)
                        st.error(t("login.rate_limited", minutes=minutes))
                        return

                    user = login(db, email, password)
                    if user:
                        record_login_attempt(db, email, True)
                        clear_login_attempts(db, email)
                        st.session_state["user_id"] = str(user.id)
                        st.session_state["username"] = user.username
                        st.session_state["is_admin"] = bool(user.is_admin)
                        st.session_state["logged_in"] = True
                        st.rerun()
                    else:
                        record_login_attempt(db, email, False)
                        st.error(t("login.invalid"))
                finally:
                    db.close()

    with tab_register:
        reg_email = st.text_input(t("login.email"), key="reg_email")
        reg_username = st.text_input(t("login.username"), key="reg_username")
        reg_password = st.text_input(t("login.password"), type="password", key="reg_password")

        if reg_password:
            strength = password_strength(reg_password)
            label_key = f"login.pw_strength_{strength}"
            colors = {"weak": "red", "medium": "orange", "strong": "green"}
            st.caption(f":{colors[strength]}[{t(label_key)}]")

        reg_confirm = st.text_input(t("login.confirm_password"), type="password", key="reg_confirm")
        accept_terms = st.checkbox(t("login.accept_terms"), key="accept_terms")
        with st.expander(t("login.read_terms")):
            st.markdown(t("terms.section_a"))
            st.markdown(t("terms.section_b"))
            st.markdown(t("terms.section_c"))
            st.markdown(t("terms.section_d"))
            st.caption(t("terms.last_updated"))
        reg_submitted = st.button(t("login.btn_register"))

        if reg_submitted:
            if not reg_email or not reg_username or not reg_password:
                st.error(t("login.fill_all"))
                return

            if not is_valid_email(reg_email):
                st.error(t("login.invalid_email"))
                return

            if not accept_terms:
                st.error(t("login.terms_required"))
                return

            if reg_password != reg_confirm:
                st.error(t("login.pw_mismatch"))
                return

            if len(reg_password) < 8:
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
