import streamlit as st

from db.models import Story
from db.session import SessionLocal
from storage.file_store import read_file_bytes


def show_library_page():
    st.markdown("## My Library")

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
            st.info("You haven't created any stories yet. Go to 'Create Story' to get started!")
            return

        # Auto-refresh if any stories are still processing
        has_pending = any(s.status in ("generating", "tts_processing") for s in stories)

        for story in stories:
            _render_story_card(story)

        if has_pending:
            st.markdown("---")
            if st.button("Refresh Status"):
                st.rerun()
            st.caption("Some stories are still being processed. Click refresh to check status.")

    finally:
        db.close()


def _render_story_card(story: Story):
    status_class = f"status-{story.status}"
    status_label = {
        "generating": "Generating Story",
        "tts_processing": "Creating Audio",
        "ready": "Ready",
        "failed": "Failed",
    }.get(story.status, story.status)

    with st.container():
        st.markdown(
            f'<div class="story-card">'
            f'<span class="{status_class} status-badge">{status_label}</span>'
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
                    st.markdown("*No cover*")
            else:
                st.markdown("*No cover*")

        with col_info:
            st.markdown(f"### {story.title}")
            st.markdown(f"**Mood:** {story.mood or 'N/A'} | **Age:** {story.age_range or 'N/A'}")

            if story.summary:
                st.caption(story.summary)

            if story.status == "ready" and story.audio_path:
                audio_bytes = read_file_bytes(story.audio_path)
                if audio_bytes:
                    st.audio(audio_bytes, format="audio/mp3")

                    if story.duration_seconds:
                        minutes = int(story.duration_seconds // 60)
                        seconds = int(story.duration_seconds % 60)
                        st.caption(f"Duration: {minutes}:{seconds:02d}")

                    st.download_button(
                        label="Download MP3",
                        data=audio_bytes,
                        file_name=f"{story.title}.mp3",
                        mime="audio/mpeg",
                        key=f"download_{story.id}",
                    )

            elif story.status == "failed":
                st.error("Audio generation failed. Try creating the story again.")

        st.divider()
