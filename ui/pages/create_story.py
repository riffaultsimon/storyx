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

logger = logging.getLogger(__name__)


def show_create_story_page():
    st.markdown("## Create a New Story")

    # Credit balance check
    db = SessionLocal()
    try:
        balance = check_balance(db, st.session_state["user_id"])
    finally:
        db.close()

    st.markdown(f"**Credits remaining:** {balance}")
    if balance < 1:
        st.warning("You need at least 1 credit to generate a story.")
        if st.button("Buy Credits"):
            st.session_state["_nav"] = "Buy Credits"
            st.rerun()
        return

    with st.form("story_form"):
        col1, col2 = st.columns(2)

        with col1:
            topic = st.text_input(
                "What should the story be about?",
                placeholder="e.g., A brave little rabbit who learns to share",
            )
            setting = st.text_input(
                "Where does it take place?",
                placeholder="e.g., A magical forest, a seaside village",
            )
            mood = st.selectbox("Mood", MOODS)

        with col2:
            age_range = st.selectbox("Age Range", AGE_RANGES)
            story_length = st.selectbox("Story Length", STORY_LENGTHS)

        submitted = st.form_submit_button("Generate Story")

    if submitted:
        if not topic or not setting:
            st.error("Please provide a topic and setting.")
            return

        _handle_story_generation(topic, setting, mood, age_range, story_length)

    # Show preview if story was just generated
    if st.session_state.get("preview_story"):
        _show_story_preview()


def _handle_story_generation(topic, setting, mood, age_range, story_length):
    with st.spinner("Crafting your story..."):
        try:
            structured, usage = generate_story(topic, setting, mood, age_range, story_length)
        except Exception as e:
            st.error(f"Story generation failed: {e}")
            logger.exception("Story generation failed")
            return

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
        st.info(f"Moral: {structured.moral}")

    with st.expander("Characters", expanded=False):
        for ch in structured.characters:
            st.markdown(f"- **{ch.name}** (age {ch.age}, {ch.gender}): {ch.description}")

    with st.expander("Story Segments", expanded=True):
        for seg in structured.segments:
            if seg.type == "narration":
                st.markdown(f"*{seg.text}*")
            else:
                st.markdown(f"**{seg.character}** ({seg.emotion}): \"{seg.text}\"")

    col_save, col_discard = st.columns(2)

    with col_save:
        if st.button("Save & Generate Audio"):
            _save_and_generate(structured, params)

    with col_discard:
        if st.button("Discard"):
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
            st.error("Insufficient credits. Please buy more credits.")
            return

        # Generate cover image
        cover_path = None
        cover_cost = 0.0
        try:
            with st.spinner("Generating cover image..."):
                image_url = generate_cover_image(structured.summary, structured.title)
                cover_path = download_and_save_image(image_url, story_id)
                cover_cost = estimate_cover_cost()
        except Exception as e:
            logger.warning("Cover generation failed: %s", e)
            st.warning("Cover image generation failed, continuing without it.")

        # Estimate story generation cost
        usage = st.session_state.get("story_usage", {})
        gen_cost = estimate_story_generation_cost(
            usage.get("prompt_tokens", 0),
            usage.get("completion_tokens", 0),
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

        st.success(f"Story '{structured.title}' saved! Audio is being generated.")
        st.info("Check your library for progress.")

    except Exception as e:
        db.rollback()
        st.error(f"Failed to save story: {e}")
        logger.exception("Failed to save story")
    finally:
        db.close()
