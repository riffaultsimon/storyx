import streamlit as st
from streamlit_extras.stylable_container import stylable_container

from db.session import init_db, SessionLocal
from ui.theme import inject_custom_css
from ui.pages.login import show_login_page
from ui.pages.create_story import show_create_story_page
from ui.pages.library import show_library_page
from ui.pages.account import show_account_page
from ui.pages.buy_credits import show_buy_credits_page
from ui.pages.admin import show_admin_page
from credits.service import check_balance
from i18n import t, LANGUAGES

# --- CONFIGURATION ---
st.set_page_config(
    page_title="Storyx",
    page_icon="🐙",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_custom_css()
init_db()

# --- REUSABLE MOSAIC TILE COMPONENT ---
def nav_tile(label, icon, target_page):
    """Creates a square-ish orange tile for sidebar navigation."""
    is_active = st.session_state.get("page") == target_page

    # Orange shades: Bright for active, slightly deeper for inactive
    bg_color = "#FF8C00" if is_active else "#E67E22"
    border_style = "2px solid white" if is_active else "1px solid rgba(255,255,255,0.1)"

    with stylable_container(
        key=f"nav_container_{target_page}",
        css_styles=f"""
            button {{
                background-color: {bg_color};
                color: white;
                border-radius: 12px;
                height: 90px;
                width: 100%;
                border: {border_style} !important;
                margin-bottom: -10px;
                transition: all 0.2s ease-in-out;
            }}
            button:hover {{
                background-color: #FFA502 !important;
                transform: scale(1.03);
                border: 2px solid white !important;
            }}
            button p {{
                font-weight: bold;
                font-size: 1rem;
                white-space: pre-line;
            }}
        """,
    ):
        if st.button(f"{icon}\n{label}", key=f"btn_{target_page}"):
            st.session_state.page = target_page
            st.rerun()

# --- STRIPE REDIRECT HANDLING ---
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
                st.success(t("app.payment_success", credits=result['credits']))
            st.query_params.clear()
        finally:
            db.close()
        return

    if params.get("stripe_cancelled"):
        st.info(t("app.payment_cancelled"))
        st.query_params.clear()

# --- MAIN APP LOGIC ---
if not st.session_state.get("logged_in"):
    show_login_page()
else:
    _handle_stripe_return()

    # Initialize default page
    if "page" not in st.session_state:
        st.session_state.page = "Create Story"

    # --- SIDEBAR NAVIGATION ---
    with st.sidebar:
        st.markdown(
            '<div class="main-header"><h1 style="font-size:2.2rem; color:#FF8C00;">Storyx 🐙</h1></div>',
            unsafe_allow_html=True,
        )
        st.markdown(t("app.welcome", username=st.session_state.get('username', 'Explorer')))

        # Language selector
        lang_codes = list(LANGUAGES.keys())
        lang_labels = list(LANGUAGES.values())
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

        # Credit Balance Display
        db = SessionLocal()
        try:
            balance = check_balance(db, st.session_state["user_id"])
        finally:
            db.close()

        st.info(t("app.balance", balance=balance))
        st.divider()

        # Mosaic Grid Layout
        st.write(f"### {t('app.menu')}")
        col1, col2 = st.columns(2)

        with col1:
            nav_tile(t("app.nav.create"), "✍️", "Create Story")
            nav_tile(t("app.nav.credits"), "💳", "Buy Credits")
            # Admin tile appears in the left column if user is admin
            if st.session_state.get("is_admin"):
                nav_tile(t("app.nav.admin"), "🔐", "Admin")

        with col2:
            nav_tile(t("app.nav.library"), "📚", "My Library")
            nav_tile(t("app.nav.account"), "👤", "Account")

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
