import streamlit as st
from streamlit_extras.stylable_container import stylable_container

from db.session import init_db, SessionLocal
from ui.theme import inject_custom_css
from ui.pages.login import show_login_page
from ui.pages.landing import show_landing_page
from ui.pages.create_story import show_create_story_page
from ui.pages.library import show_library_page
from ui.pages.account import show_account_page
from ui.pages.buy_credits import show_buy_credits_page
from ui.pages.admin import show_admin_page
from ui.pages.terms import show_terms_page
from ui.pages.privacy import show_privacy_page
from credits.service import check_balance
from i18n import t, LANGUAGES, lang_selector

# --- CONFIGURATION ---
st.set_page_config(
    page_title="storyx",
    page_icon="🐙",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_custom_css()
init_db()

# --- REUSABLE NAV ITEM COMPONENT ---
def nav_item(label, icon, target_page):
    """Creates an icon + label row for sidebar navigation."""
    is_active = st.session_state.get("page") == target_page

    bg = "rgba(255, 140, 0, 0.15)" if is_active else "transparent"
    border_left = "3px solid #FF8C00" if is_active else "3px solid transparent"
    text_color = "#FF8C00" if is_active else "#5D4E37"
    font_weight = "700" if is_active else "500"

    with stylable_container(
        key=f"nav_{target_page}",
        css_styles=[
            f"""button {{
                background: {bg} !important;
                border: none !important;
                border-left: {border_left} !important;
                border-radius: 0 8px 8px 0 !important;
                width: 100%;
                padding: 0.55rem 0.75rem !important;
                margin-bottom: 2px;
                text-align: left !important;
                transition: all 0.15s ease;
            }}""",
            f"""button:hover {{
                background: rgba(255, 140, 0, 0.10) !important;
                border-left: 3px solid #FFA502 !important;
            }}""",
            f"""button p {{
                color: {text_color} !important;
                font-weight: {font_weight};
                font-size: 0.9rem;
                margin: 0 !important;
            }}""",
        ],
    ):
        if st.button(f"{icon}  {label}", key=f"btn_{target_page}"):
            st.session_state.page = target_page
            st.rerun()

# --- GOOGLE OAUTH HANDLING ---
def _handle_google_callback() -> bool:
    """Handle Google OAuth callback and log in the user.

    Returns True if user was logged in via Google, False otherwise.
    """
    params = st.query_params

    # Check if this is a Google callback
    if not params.get("google_callback"):
        return False

    code = params.get("code")
    error = params.get("error")

    # Clear query params early
    st.query_params.clear()

    if error:
        st.error(t("login.google_error", error=error))
        return False

    if not code:
        st.error(t("login.google_no_code"))
        return False

    # Exchange code for user info
    from auth.google_oauth import authenticate_with_google
    from auth.service import get_or_create_google_user

    user_info = authenticate_with_google(code)
    if not user_info or not user_info.get("google_id"):
        st.error(t("login.google_failed"))
        return False

    # Get or create user
    db = SessionLocal()
    try:
        user = get_or_create_google_user(
            db,
            google_id=user_info["google_id"],
            email=user_info["email"],
            name=user_info.get("name", ""),
        )

        # Set session state
        st.session_state["user_id"] = str(user.id)
        st.session_state["username"] = user.username
        st.session_state["is_admin"] = bool(user.is_admin)
        st.session_state["logged_in"] = True

        return True
    except Exception as e:
        st.error(t("login.google_failed"))
        return False
    finally:
        db.close()


# --- STRIPE REDIRECT HANDLING ---
def _handle_stripe_return_before_login() -> bool:
    """Check for Stripe redirect and restore session if needed.

    Returns True if user session was restored from Stripe, False otherwise.
    """
    params = st.query_params
    session_id = params.get("stripe_session_id")

    if not session_id:
        return False

    # Already logged in - just process normally
    if st.session_state.get("logged_in"):
        return False

    # Not logged in - try to restore session from Stripe metadata
    from credits.stripe_checkout import get_session_user
    from db.models import User

    session_info = get_session_user(session_id)
    if not session_info:
        st.query_params.clear()
        return False

    # Restore user session
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == session_info["user_id"]).first()
        if user:
            st.session_state["user_id"] = str(user.id)
            st.session_state["username"] = user.username
            st.session_state["is_admin"] = bool(user.is_admin)
            st.session_state["logged_in"] = True
            return True
    finally:
        db.close()

    return False


def _handle_stripe_return():
    """Check for Stripe redirect and fulfill payment if present."""
    params = st.query_params
    session_id = params.get("stripe_session_id")

    if session_id:
        from credits.stripe_checkout import verify_and_fulfill
        db = SessionLocal()
        try:
            result = verify_and_fulfill(db, session_id)
            if result:
                if result.get("already_fulfilled"):
                    st.info(t("app.payment_already_processed"))
                else:
                    st.success(t("app.payment_success", credits=result['credits']))
                # Navigate to Buy Credits page to show updated balance
                st.session_state.page = "Buy Credits"
            st.query_params.clear()
        finally:
            db.close()
        return

    if params.get("stripe_cancelled"):
        st.info(t("app.payment_cancelled"))
        st.query_params.clear()

# --- MAIN APP LOGIC ---
# Handle OAuth callbacks before login check
_handle_google_callback()
_handle_stripe_return_before_login()

if not st.session_state.get("logged_in"):
    _guest_page = st.session_state.get("page")
    if _guest_page == "Privacy Policy":
        show_privacy_page()
        if st.button(t("app.back_to_home")):
            st.session_state.pop("page", None)
            st.rerun()
    elif _guest_page == "Terms":
        show_terms_page()
        if st.button(t("app.back_to_home")):
            st.session_state.pop("page", None)
            st.rerun()
    elif _guest_page == "Login":
        show_login_page()
    else:
        show_landing_page()
else:
    _handle_stripe_return()

    # Initialize default page (also redirect away from guest-only pages)
    if st.session_state.get("page") in (None, "Login", ""):
        st.session_state.page = "Create Story"

    # --- SIDEBAR NAVIGATION ---
    with st.sidebar:
        st.markdown(
            '<div class="main-header"><h1 style="font-size:2.2rem; color:#FF8C00;">storyx <span class="header-octopus">🐙</span></h1></div>',
            unsafe_allow_html=True,
        )
        st.markdown(t("app.welcome", username=st.session_state.get('username', 'Explorer')))

        lang_selector()

        # Credit Balance Display
        db = SessionLocal()
        try:
            balance = check_balance(db, st.session_state["user_id"])
        finally:
            db.close()

        st.info(t("app.balance", balance=balance))
        st.divider()

        # Navigation List
        nav_item(t("app.nav.create"), "✍️", "Create Story")
        nav_item(t("app.nav.library"), "📚", "My Library")
        nav_item(t("app.nav.credits"), "💳", "Buy Credits")
        nav_item(t("app.nav.account"), "👤", "Account")
        nav_item(t("app.nav.terms"), "📜", "Terms")
        if st.session_state.get("is_admin"):
            nav_item(t("app.nav.admin"), "🔐", "Admin")

        st.divider()

        # Logout Button
        if st.button(t("app.logout"), use_container_width=True, type="secondary"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    # --- PAGE ROUTING ---
    page = st.session_state.page

    if page == "Create Story":
        show_create_story_page()
    elif page == "My Library":
        show_library_page()
    elif page == "Buy Credits":
        show_buy_credits_page()
    elif page == "Account":
        show_account_page()
    elif page == "Admin":
        show_admin_page()
    elif page == "Terms":
        show_terms_page()
    elif page == "Privacy Policy":
        show_privacy_page()

# --- FOOTER ---
st.markdown(
    """
    <div class="storyx-footer">
        <div class="footer-brand"><span class="header-octopus">🐙</span> &copy; 2026 Storyx</div>
        A trade name of [Your Company] SRL. Registered Office: [Address], Belgium<br>
        VAT: BE 0123.456.789 <span class="footer-separator">|</span> RPM [City]<br><br>
        <em>Transparency Notice: This service uses a hybrid of user-recorded audio and AI-generated narration.
        AI-generated segments are marked within the application.</em>
        <div style="display:flex;align-items:center;justify-content:center;gap:5px;margin-top:0.75rem;opacity:0.65;">
            <span style="font-size:0.7rem;color:#636E72;">Powered by</span>
            <span style="font-weight:700;color:#635BFF;font-size:0.85rem;font-family:system-ui,sans-serif;letter-spacing:-0.5px;">stripe</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

_fc1, _fc2, _fc3 = st.columns([1, 2, 1])
with _fc2:
    with stylable_container(
        key="footer_links",
        css_styles=[
            """button {
                background-color: white !important;
                background-image: none !important;
                border: 2px solid #FF8C00 !important;
                border-radius: 20px !important;
                color: #FF8C00 !important;
                height: auto !important;
                min-height: 0px !important;
                padding: 4px 15px !important;
            }""",
            """button p {
                color: #FF8C00 !important;
                font-size: 0.8rem !important;
                font-weight: 600 !important;
            }""",
            """button:hover {
                background-color: rgba(255, 140, 0, 0.08) !important;
                border-color: #FF8C00 !important;
            }""",
        ],
    ):
    # ... your columns and buttons ...
        _fl1, _fl2 = st.columns(2)
        with _fl1:
            if st.button("Privacy Policy", key="footer_privacy"):
                st.session_state.page = "Privacy Policy"
                st.rerun()
        with _fl2:
            if st.button("Terms of Service", key="footer_terms"):
                st.session_state.page = "Terms"
                st.rerun()
