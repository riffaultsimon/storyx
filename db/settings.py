"""Read/write application-wide settings (singleton row)."""

from sqlalchemy.orm import Session
from db.models import AppSettings


def get_settings(db: Session) -> AppSettings:
    """Return the singleton settings row, creating it if needed."""
    settings = db.query(AppSettings).filter(AppSettings.id == "default").first()
    if not settings:
        settings = AppSettings(id="default")
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


def update_settings(db: Session, **kwargs) -> AppSettings:
    """Update settings fields. Only known columns are applied."""
    settings = get_settings(db)
    allowed = {
        "image_provider", "bgm_enabled", "bgm_provider",
        "story_model", "tts_model",
    }
    for key, value in kwargs.items():
        if key in allowed:
            setattr(settings, key, value)
    db.commit()
    db.refresh(settings)
    return settings
