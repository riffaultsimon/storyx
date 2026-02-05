import streamlit as st

from i18n import t


def show_privacy_page():
    st.markdown(f"## {t('privacy.title')}")
    st.markdown(t("privacy.section_a"))
    st.markdown(t("privacy.section_b"))
    st.markdown(t("privacy.section_c"))
    st.markdown(t("privacy.section_d"))
    st.markdown(t("privacy.section_e"))
    st.markdown(t("privacy.section_f"))
    st.markdown(t("privacy.section_g"))
    st.caption(t("privacy.last_updated"))
