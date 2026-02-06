import streamlit as st
from streamlit_extras.stylable_container import stylable_container

from i18n import t, LANGUAGES


def show_landing_page():
    # Language selector
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

    # --- Hero Section ---
    st.markdown(
        '<div class="landing-hero">'
        '<div class="header-octopus" style="font-size: 5rem;">🐙</div>'
        f'<h1><span class="typewriter-title">{t("landing.hero_title")}</span></h1>'
        f'<p class="typewriter-subtitle">{t("landing.hero_subtitle")}</p>'
        "</div>",
        unsafe_allow_html=True,
    )

    # --- CTA Buttons ---
    _pad1, btn_left, btn_right, _pad2 = st.columns([2, 1, 1, 2])
    with btn_left:
        with stylable_container(
            key="cta_start",
            css_styles="""
                button {
                    background: linear-gradient(135deg, #FF6B6B, #FF8E8E) !important;
                    color: white !important;
                    border: none !important;
                    border-radius: 30px !important;
                    padding: 0.75rem 2.5rem !important;
                    font-size: 1.1rem !important;
                    font-weight: 700 !important;
                    width: 100%;
                    transition: all 0.3s ease;
                }
                button:hover {
                    transform: translateY(-3px) !important;
                    box-shadow: 0 6px 20px rgba(255, 107, 107, 0.5) !important;
                }
                button p { color: white !important; }
            """,
        ):
            if st.button(t("landing.cta_start"), key="landing_get_started"):
                st.session_state.page = "Login"
                st.rerun()

    with btn_right:
        with stylable_container(
            key="cta_login",
            css_styles="""
                button {
                    background: white !important;
                    color: #FF8C00 !important;
                    border: 2px solid #FF8C00 !important;
                    border-radius: 30px !important;
                    padding: 0.75rem 2.5rem !important;
                    font-size: 1.1rem !important;
                    font-weight: 700 !important;
                    width: 100%;
                    transition: all 0.3s ease;
                }
                button:hover {
                    background: rgba(255, 140, 0, 0.08) !important;
                    transform: translateY(-3px) !important;
                    box-shadow: 0 6px 20px rgba(255, 140, 0, 0.3) !important;
                }
                button p { color: #FF8C00 !important; }
            """,
        ):
            if st.button(t("landing.cta_login"), key="landing_login"):
                st.session_state.page = "Login"
                st.rerun()

    # --- Features Section ---
    st.markdown(
        f'<div class="landing-features-title">{t("landing.features_title")}</div>',
        unsafe_allow_html=True,
    )

    feat1, feat2, feat3 = st.columns(3)

    with feat1:
        st.markdown(
            '<div class="feature-card">'
            '<div class="feature-icon">✍️</div>'
            f'<div class="feature-card-title">{t("landing.feature_1_title")}</div>'
            f'<div class="feature-card-desc">{t("landing.feature_1_desc")}</div>'
            "</div>",
            unsafe_allow_html=True,
        )

    with feat2:
        st.markdown(
            '<div class="feature-card">'
            '<div class="feature-icon">🎙️</div>'
            f'<div class="feature-card-title">{t("landing.feature_2_title")}</div>'
            f'<div class="feature-card-desc">{t("landing.feature_2_desc")}</div>'
            "</div>",
            unsafe_allow_html=True,
        )

    with feat3:
        st.markdown(
            '<div class="feature-card">'
            '<div class="feature-icon">📚</div>'
            f'<div class="feature-card-title">{t("landing.feature_3_title")}</div>'
            f'<div class="feature-card-desc">{t("landing.feature_3_desc")}</div>'
            "</div>",
            unsafe_allow_html=True,
        )
