"""Internationalization support for StoryX."""

import json
import os
import streamlit as st

_LANG_DIR = os.path.dirname(__file__)
_cache: dict[str, dict] = {}

LANGUAGES = {
    "fr": "🇫🇷 Français",
    "en": "🇬🇧 English",
    "de": "🇩🇪 Deutsch",
    "es": "🇪🇸 Español",
}


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
