import logging
import uuid

import streamlit as st

from config import AGE_RANGES, MOODS, STORY_LENGTHS
from db.models import Story
from db.session import SessionLocal
from story.generator import generate_story
from story.cover import generate_cover_image
from storage.file_store import download_and_save_image
from workers.story_worker import submit_tts_job
from credits.service import check_balance, deduct_credit
from credits.cost_tracker import (
    estimate_story_generation_cost,
    estimate_cover_cost,
)
from i18n import t

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
            topic = st.text_input(
                t("create.topic_label"),
                placeholder=t("create.topic_placeholder"),
            )
            setting = st.text_input(
                t("create.setting_label"),
                placeholder=t("create.setting_placeholder"),
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

        _handle_story_generation(topic, setting, mood, age_range, story_length)

    # Show preview if story was just generated
    if st.session_state.get("preview_story"):
        _show_story_preview()


def _handle_story_generation(topic, setting, mood, age_range, story_length):
    with st.spinner(t("create.generating")):
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
    }
    st.rerun()


def _show_story_preview():
    structured = st.session_state["preview_story"]
    params = st.session_state["story_params"]

    st.markdown(f"### {structured.title}")
    st.markdown(f"*{structured.summary}*")

    if structured.moral:
        st.info(t("create.moral", moral=structured.moral))

    with st.expander(t("create.characters"), expanded=False):
        for ch in structured.characters:
            st.markdown(f"- **{ch.name}** (age {ch.age}, {ch.gender}): {ch.description}")

    with st.expander(t("create.segments"), expanded=True):
        for seg in structured.segments:
            if seg.type == "narration":
                st.markdown(f"*{seg.text}*")
            else:
                st.markdown(f"**{seg.character}** ({seg.emotion}): \"{seg.text}\"")

    col_save, col_discard = st.columns(2)

    with col_save:
        if st.button(t("create.btn_save")):
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

        # Deduct credit
        if not deduct_credit(db, user_id, story_id):
            st.error(t("create.insufficient"))
            return

        # Generate cover image
        cover_path = None
        cover_cost = 0.0
        try:
            from db.settings import get_settings
            settings = get_settings(db)
            image_provider = settings.image_provider

            with st.spinner(t("create.gen_cover")):
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
            story_json=structured.model_dump(),
            summary=structured.summary,
            cover_image_path=cover_path,
            status="tts_processing",
            cost_story_generation=round(gen_cost, 6),
            cost_cover_image=round(cover_cost, 6),
            segment_count=len(structured.segments),
        )
        db.add(story)
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
