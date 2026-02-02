import streamlit as st

from i18n import t


def show_terms_page():
    st.markdown(f"## {t('terms.title')}")
    st.markdown(t("terms.section_a"))
    st.markdown(t("terms.section_b"))
    st.markdown(t("terms.section_c"))
    st.markdown(t("terms.section_d"))
    st.caption(t("terms.last_updated"))
