"""Internationalization support for StoryX."""

import json
import os
import streamlit as st

_LANG_DIR = os.path.dirname(__file__)
_cache: dict[str, dict] = {}

LANGUAGES = {
    "fr": "Français",
    "en": "English",
    "de": "Deutsch",
    "es": "Español",
}

# ISO country codes for flag images (en → gb for the UK flag)
_FLAG_CODES = {"fr": "fr", "en": "gb", "de": "de", "es": "es"}


def _load_lang(code: str) -> dict:
    if code not in _cache:
        path = os.path.join(_LANG_DIR, f"{code}.json")
        with open(path, "r", encoding="utf-8") as f:
            _cache[code] = json.load(f)
    return _cache[code]


def get_lang() -> str:
    return st.session_state.get("lang", "fr")


def t(key: str, **kwargs) -> str:
    """Translate a key, with optional format kwargs."""
    lang = get_lang()
    strings = _load_lang(lang)
    text = strings.get(key)
    if text is None:
        # Fallback to English
        text = _load_lang("en").get(key, key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, IndexError):
            return text
    return text


def lang_selector():
    """Render a compact language selector with flag images + pills."""
    current = st.session_state.get("lang", "fr")

    # Flag images row (decorative, shows which is active)
    flag_imgs = []
    for code in LANGUAGES:
        fc = _FLAG_CODES[code]
        active = code == current
        style = (
            "border:2px solid #FF8C00;border-radius:3px;"
            if active
            else "opacity:0.4;border:2px solid transparent;border-radius:3px;"
        )
        flag_imgs.append(
            f'<img src="https://flagcdn.com/28x21/{fc}.png" '
            f'alt="{code.upper()}" title="{LANGUAGES[code]}" style="{style}">'
        )

    st.markdown(
        '<div style="display:flex;gap:8px;justify-content:center;margin-bottom:2px;">'
        + "".join(flag_imgs)
        + "</div>",
        unsafe_allow_html=True,
    )

    # Pills selector (clickable)
    lang_codes = list(LANGUAGES.keys())
    selected = st.pills(
        "lang",
        options=lang_codes,
        default=current,
        format_func=lambda c: LANGUAGES[c],
        label_visibility="collapsed",
    )
    if selected and selected != current:
        st.session_state["lang"] = selected
        st.rerun()
