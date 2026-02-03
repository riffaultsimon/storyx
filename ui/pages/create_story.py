import logging
import uuid

import streamlit as st

from config import AGE_RANGES, MOODS, STORY_LENGTHS
from db.models import Story
from db.session import SessionLocal
from story.generator import generate_story
from story.cover import generate_cover_image
from storage.file_store import download_and_save_image, save_recording
from audio.effects import apply_effect
from workers.story_worker import submit_tts_job
from credits.service import check_balance, deduct_credit
from credits.cost_tracker import (
    estimate_story_generation_cost,
    estimate_cover_cost,
)
from i18n import t, get_lang
from ui.loader import storyx_loader

logger = logging.getLogger(__name__)


def show_create_story_page():
    st.markdown(f"## {t('create.header')}")

    # Credit balance check
    db = SessionLocal()
    try:
        balance = check_balance(db, st.session_state["user_id"])
    finally:
        db.close()

    st.markdown(t("create.credits_remaining", balance=balance))
    if balance < 1:
        st.warning(t("create.no_credits"))
        if st.button(t("create.buy_credits")):
            st.session_state["_nav"] = "Buy Credits"
            st.rerun()
        return

    with st.form("story_form"):
        col1, col2 = st.columns(2)

        with col1:
            topic = st.text_area(
                t("create.topic_label"),
                placeholder=t("create.topic_placeholder"),
                height=100,
            )
            setting = st.text_area(
                t("create.setting_label"),
                placeholder=t("create.setting_placeholder"),
                height=100,
            )
            mood = st.selectbox(
                t("create.mood"),
                MOODS,
                format_func=lambda m: t(f"create.mood.{m}"),
            )

        with col2:
            age_range = st.selectbox(t("create.age_range"), AGE_RANGES)
            story_length = st.selectbox(
                t("create.story_length"),
                STORY_LENGTHS,
                format_func=lambda s: t(f"create.story_length.{s}"),
            )

        submitted = st.form_submit_button(t("create.btn_generate"))

    if submitted:
        if not topic or not setting:
            st.error(t("create.need_topic"))
            return

        _handle_story_generation(topic, setting, mood, age_range, story_length, get_lang())

    # Show preview if story was just generated
    if st.session_state.get("preview_story"):
        _show_story_preview()


def _handle_story_generation(topic, setting, mood, age_range, story_length, language="en"):
    with storyx_loader(t("create.generating")):
        try:
            from db.settings import get_settings
            _db = SessionLocal()
            try:
                _settings = get_settings(_db)
                _story_model = _settings.story_model
            finally:
                _db.close()
            structured, usage = generate_story(
                topic, setting, mood, age_range, story_length,
                model_override=_story_model,
                language=language,
            )
        except Exception as e:
            st.error(t("create.gen_failed", error=e))
            logger.exception("Story generation failed")
            return

    usage["story_model"] = _story_model
    st.session_state["preview_story"] = structured
    st.session_state["story_usage"] = usage
    st.session_state["story_params"] = {
        "topic": topic,
        "setting": setting,
        "mood": mood,
        "age_range": age_range,
        "story_length": story_length,
        "language": language,
    }
    st.rerun()


def _show_story_preview():
    structured = st.session_state["preview_story"]
    params = st.session_state["story_params"]

    st.markdown(f"### {t('create.preview_title')}")
    st.caption(t("create.preview_hint"))

    edited_title = st.text_input(
        t("create.edit_title"), value=structured.title, key="edit_title",
    )
    edited_summary = st.text_area(
        t("create.edit_summary"), value=structured.summary, key="edit_summary", height=80,
    )
    edited_moral = st.text_input(
        t("create.edit_moral"), value=structured.moral or "", key="edit_moral",
    )

    with st.expander(t("create.characters"), expanded=False):
        for ch in structured.characters:
            st.markdown(f"- **{ch.name}** (age {ch.age}, {ch.gender}): {ch.description}")

    # Build a stable color map for characters
    _CHAR_COLORS = [
        "#E17055", "#00B894", "#6C5CE7", "#FDCB6E",
        "#00CEC9", "#D63031", "#A29BFE", "#FF7675",
    ]
    char_names = list(dict.fromkeys(
        seg.character for seg in structured.segments if seg.character
    ))
    char_color_map = {
        name: _CHAR_COLORS[i % len(_CHAR_COLORS)]
        for i, name in enumerate(char_names)
    }

    with st.expander(t("create.segments"), expanded=True):
        edited_segments = []
        for seg in structured.segments:
            if seg.type == "narration":
                badge_html = (
                    f'<span class="seg-badge seg-narrator">'
                    f'&#128214; {t("create.seg_narration")} #{seg.segment_id}'
                    f'</span>'
                )
                label = f"{t('create.seg_narration')} #{seg.segment_id}"
            else:
                color = char_color_map.get(seg.character, "#636E72")
                badge_html = (
                    f'<span class="seg-badge" style="background:{color};">'
                    f'&#128172; {seg.character} ({seg.emotion}) #{seg.segment_id}'
                    f'</span>'
                )
                label = f"{seg.character} ({seg.emotion}) #{seg.segment_id}"

            st.markdown(badge_html, unsafe_allow_html=True)

            col_text, col_rec = st.columns([3, 1])
            with col_text:
                new_text = st.text_area(
                    label, value=seg.text, key=f"seg_{seg.segment_id}",
                    height=80, label_visibility="collapsed",
                )
            with col_rec:
                fx_options = [
                    "clean", "robot", "fairy", "monster", "echo", "underwater",
                ]
                fx_labels = [t(f"create.fx_{fx}") for fx in fx_options]
                st.selectbox(
                    t("create.voice_effect"),
                    options=fx_options,
                    format_func=lambda v, _l=fx_labels, _o=fx_options: _l[_o.index(v)],
                    key=f"fx_{seg.segment_id}",
                )
                rec_key = f"rec_{seg.segment_id}"
                recording = st.audio_input(
                    t("create.record_voice"), key=rec_key,
                )
                if recording:
                    st.audio(recording, format="audio/wav")
                    st.caption(t("create.recording_saved"))

            edited_segments.append((seg.segment_id, new_text))

    col_save, col_discard = st.columns(2)

    with col_save:
        if st.button(t("create.btn_save")):
            # Apply edits back to the structured story
            structured.title = edited_title.strip() or structured.title
            structured.summary = edited_summary.strip() or structured.summary
            structured.moral = edited_moral.strip() or None
            for seg_id, new_text in edited_segments:
                seg = next((s for s in structured.segments if s.segment_id == seg_id), None)
                if seg and new_text.strip():
                    seg.text = new_text.strip()
            st.session_state["preview_story"] = structured
            _save_and_generate(structured, params)

    with col_discard:
        if st.button(t("create.btn_discard")):
            del st.session_state["preview_story"]
            del st.session_state["story_params"]
            st.rerun()


def _save_and_generate(structured, params):
    db = SessionLocal()
    try:
        story_id = str(uuid.uuid4())
        user_id = st.session_state["user_id"]

        # Collect user voice recordings from session state
        recordings = {}
        for seg in structured.segments:
            rec = st.session_state.get(f"rec_{seg.segment_id}")
            if rec:
                raw_bytes = rec.read()
                fx = st.session_state.get(f"fx_{seg.segment_id}", "clean")
                if fx and fx.lower() != "clean":
                    raw_bytes = apply_effect(raw_bytes, fx)
                path = save_recording(story_id, seg.segment_id, raw_bytes)
                recordings[seg.segment_id] = path

        # Deduct credit (story_id=None because the story row doesn't exist yet;
        # we link the transaction to the story after it is committed)
        credit_txn = deduct_credit(db, user_id, story_id=None)
        if credit_txn is None:
            st.error(t("create.insufficient"))
            return

        # Generate cover image
        cover_path = None
        cover_cost = 0.0
        try:
            from db.settings import get_settings
            settings = get_settings(db)
            image_provider = settings.image_provider

            with storyx_loader(t("create.gen_cover")):
                result = generate_cover_image(
                    structured.summary, structured.title, provider=image_provider
                )
                if image_provider == "imagen3":
                    import shutil, os
                    covers_dir = os.path.join("media", "covers")
                    os.makedirs(covers_dir, exist_ok=True)
                    final_path = os.path.join(covers_dir, f"{story_id}.png")
                    if result != final_path:
                        shutil.move(result, final_path)
                    cover_path = final_path
                else:
                    cover_path = download_and_save_image(result, story_id)
                cover_cost = estimate_cover_cost(provider=image_provider)
        except Exception as e:
            logger.warning("Cover generation failed: %s", e)
            st.warning(t("create.cover_failed"))

        # Estimate story generation cost
        usage = st.session_state.get("story_usage", {})
        gen_cost = estimate_story_generation_cost(
            usage.get("prompt_tokens", 0),
            usage.get("completion_tokens", 0),
            model=usage.get("story_model", "gpt-4o"),
        )

        story = Story(
            id=story_id,
            user_id=user_id,
            title=structured.title,
            topic=params["topic"],
            setting=params["setting"],
            mood=params["mood"],
            age_range=params["age_range"],
            story_length=params["story_length"],
            language=params.get("language", "en"),
            story_json=structured.model_dump(),
            summary=structured.summary,
            cover_image_path=cover_path,
            status="tts_processing",
            cost_story_generation=round(gen_cost, 6),
            cost_cover_image=round(cover_cost, 6),
            segment_count=len(structured.segments),
            user_recordings=recordings if recordings else None,
        )
        db.add(story)
        db.commit()

        # Link the credit transaction to the newly created story
        credit_txn.story_id = story_id
        db.commit()

        # Submit TTS job
        submit_tts_job(story_id, structured)

        del st.session_state["preview_story"]
        del st.session_state["story_params"]
        st.session_state.pop("story_usage", None)

        st.success(t("create.saved", title=structured.title))
        st.info(t("create.check_library"))

    except Exception as e:
        db.rollback()
        st.error(t("create.save_failed", error=e))
        logger.exception("Failed to save story")
    finally:
        db.close()
