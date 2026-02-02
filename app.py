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
from ui.pages.terms import show_terms_page
from credits.service import check_balance
from i18n import t, LANGUAGES

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
        css_styles=f"""
            button {{
                background: {bg} !important;
                border: none !important;
                border-left: {border_left} !important;
                border-radius: 0 8px 8px 0 !important;
                width: 100%;
                padding: 0.55rem 0.75rem !important;
                margin-bottom: 2px;
                text-align: left !important;
                transition: all 0.15s ease;
            }}
            button:hover {{
                background: rgba(255, 140, 0, 0.10) !important;
                border-left: 3px solid #FFA502 !important;
            }}
            button p {{
                color: {text_color} !important;
                font-weight: {font_weight};
                font-size: 0.9rem;
                margin: 0 !important;
            }}
        """,
    ):
        if st.button(f"{icon}  {label}", key=f"btn_{target_page}"):
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
            '<div class="main-header"><h1 style="font-size:2.2rem; color:#FF8C00;">storyx 🐙</h1></div>',
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
