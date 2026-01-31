from contextlib import contextmanager
import streamlit as st


@contextmanager
def storyx_loader(message: str = "Loading..."):
    placeholder = st.empty()
    placeholder.markdown(
        f"""
        <div class="storyx-loader">
            <div class="octopus">🐙</div>
            <div class="loader-text">{message}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    try:
        yield
    finally:
        placeholder.empty()
