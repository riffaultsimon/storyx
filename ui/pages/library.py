import base64
import os
import re

import streamlit as st

from db.models import Story
from db.session import SessionLocal
from storage.file_store import read_file_bytes
from i18n import t


def _safe_filename(title: str) -> str:
    """Sanitize a story title for use as a download filename."""
    name = re.sub(r'[<>:"/\\|?*]', '', title)
    name = name.strip('. ')
    if not name:
        name = "story"
    return f"{name[:100]}.mp3"


def _download_link(audio_bytes: bytes, filename: str, label: str):
    """Render an HTML download link for an MP3 file."""
    b64 = base64.b64encode(audio_bytes).decode()
    href = (
        f'<a href="data:audio/mpeg;base64,{b64}" '
        f'download="{filename}" '
        f'style="display:inline-block;padding:0.4rem 1rem;border-radius:20px;'
        f'background:linear-gradient(135deg,#FF6B6B,#FF8E8E);color:white;'
        f'text-decoration:none;font-weight:700;font-size:0.85rem;'
        f"font-family:'Bahnschrift','Segoe UI',sans-serif;"
        f'">{label}</a>'
    )
    st.markdown(href, unsafe_allow_html=True)


def show_library_page():
    st.markdown(f"## {t('library.header')}")

    user_id = st.session_state["user_id"]
    db = SessionLocal()

    try:
        stories = (
            db.query(Story)
            .filter(Story.user_id == user_id)
            .order_by(Story.created_at.desc())
            .all()
        )

        if not stories:
            st.info(t("library.empty"))
            return

        # View toggle
        view = st.toggle(t("library.tile_view"), value=st.session_state.get("library_tile_view", False))
        st.session_state["library_tile_view"] = view

        # Handle pending delete confirmation
        _handle_delete(db)

        # Auto-refresh if any stories are still processing
        has_pending = any(s.status in ("generating", "tts_processing") for s in stories)

        if has_pending:
            st.caption(t("library.processing"))
            if st.button(t("library.refresh")):
                st.rerun()

        if view:
            _render_tile_grid(stories, db)
        else:
            for story in stories:
                _render_story_card(story, db)

    finally:
        db.close()


def _handle_delete(db):
    """Process a confirmed delete."""
    story_id = st.session_state.pop("_confirm_delete_id", None)
    if not story_id:
        return
    story = db.query(Story).filter(
        Story.id == story_id,
        Story.user_id == st.session_state["user_id"],
    ).first()
    if story:
        for path in (story.audio_path, story.cover_image_path):
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass
        db.delete(story)
        db.commit()
        st.success(t("library.deleted", title=story.title))
        st.rerun()


def _status_label(status: str) -> str:
    return t(f"library.status.{status}")


def _delete_button(story: Story):
    """Render a delete button with confirmation."""
    key = f"del_{story.id}"
    if st.session_state.get(f"_ask_delete_{story.id}"):
        st.warning(t("library.confirm_delete", title=story.title))
        col_yes, col_no = st.columns(2)
        with col_yes:
            if st.button(t("library.btn_yes_delete"), key=f"yes_{story.id}", type="primary"):
                st.session_state["_confirm_delete_id"] = story.id
                st.session_state.pop(f"_ask_delete_{story.id}", None)
                st.rerun()
        with col_no:
            if st.button(t("library.btn_cancel"), key=f"no_{story.id}"):
                st.session_state.pop(f"_ask_delete_{story.id}", None)
                st.rerun()
    else:
        if st.button(t("library.btn_delete"), key=key):
            st.session_state[f"_ask_delete_{story.id}"] = True
            st.rerun()


# ── List view ──────────────────────────────────────────────

def _render_story_card(story: Story, db):
    status_class = f"status-{story.status}"
    label = _status_label(story.status)

    with st.container():
        st.markdown(
            f'<div class="story-card">'
            f'<span class="{status_class} status-badge">{label}</span>'
            f"</div>",
            unsafe_allow_html=True,
        )

        col_img, col_info = st.columns([1, 3])

        with col_img:
            if story.cover_image_path:
                cover_bytes = read_file_bytes(story.cover_image_path)
                if cover_bytes:
                    st.image(cover_bytes, width=200)
                else:
                    st.markdown(f"*{t('library.no_cover')}*")
            else:
                st.markdown(f"*{t('library.no_cover')}*")

        with col_info:
            st.markdown(f"### {story.title}")
            st.markdown(t("library.mood_age", mood=story.mood or 'N/A', age=story.age_range or 'N/A'))

            if story.summary:
                st.caption(story.summary)

            if story.status == "ready" and story.audio_path:
                audio_bytes = read_file_bytes(story.audio_path)
                if audio_bytes:
                    st.audio(audio_bytes, format="audio/mp3")

                    if story.duration_seconds:
                        minutes = int(story.duration_seconds // 60)
                        seconds = int(story.duration_seconds % 60)
                        st.caption(t("library.duration", duration=f"{minutes}:{seconds:02d}"))

                    _download_link(audio_bytes, _safe_filename(story.title), t("library.download_mp3"))

            elif story.status == "failed":
                st.error(t("library.audio_failed"))

            _delete_button(story)

        st.divider()


# ── Tile view (3 columns) ─────────────────────────────────

def _render_tile_grid(stories: list[Story], db):
    rows = [stories[i:i + 3] for i in range(0, len(stories), 3)]
    for row in rows:
        cols = st.columns(3)
        for idx, story in enumerate(row):
            with cols[idx]:
                _render_tile(story)


def _render_tile(story: Story):
    label = _status_label(story.status)
    status_class = f"status-{story.status}"

    with st.container():
        st.markdown(
            f'<span class="{status_class} status-badge" style="font-size:0.75rem;">{label}</span>',
            unsafe_allow_html=True,
        )

        if story.cover_image_path:
            cover_bytes = read_file_bytes(story.cover_image_path)
            if cover_bytes:
                st.image(cover_bytes, use_container_width=True)

        st.markdown(f"**{story.title}**")
        st.caption(f"{story.mood or ''} | {story.age_range or ''}")

        if story.status == "ready" and story.audio_path:
            audio_bytes = read_file_bytes(story.audio_path)
            if audio_bytes:
                st.audio(audio_bytes, format="audio/mp3")
                _download_link(audio_bytes, _safe_filename(story.title), t("library.download"))

        _delete_button(story)
        st.divider()
