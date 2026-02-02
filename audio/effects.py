"""Voice effect presets applied to user recordings via pedalboard."""

import io
import logging

import numpy as np
from pedalboard import (
    Chorus,
    Delay,
    Distortion,
    Gain,
    LowpassFilter,
    Pedalboard,
    PitchShift,
    Reverb,
)
from pydub import AudioSegment

logger = logging.getLogger(__name__)

EFFECT_PRESETS = ("clean", "robot", "fairy", "monster", "echo", "underwater")


def _build_board(effect: str) -> Pedalboard | None:
    """Return a Pedalboard chain for the given effect name, or None for clean."""
    if effect == "clean":
        return None
    if effect == "robot":
        return Pedalboard([
            PitchShift(semitones=-3),
            Chorus(rate_hz=1.0, depth=0.25, mix=0.5),
            Distortion(drive_db=8),
            Gain(gain_db=3),
        ])
    if effect == "fairy":
        return Pedalboard([
            PitchShift(semitones=5),
            Reverb(room_size=0.8, wet_level=0.4),
            Gain(gain_db=3),
        ])
    if effect == "monster":
        return Pedalboard([
            PitchShift(semitones=-8),
            Reverb(room_size=0.5, wet_level=0.3),
            Gain(gain_db=4),
        ])
    if effect == "echo":
        return Pedalboard([
            Reverb(room_size=0.95, wet_level=0.5),
            Delay(delay_seconds=0.5, feedback=0.4, mix=0.5),
        ])
    if effect == "underwater":
        return Pedalboard([
            LowpassFilter(cutoff_frequency_hz=800),
            Chorus(rate_hz=0.3, depth=0.6, mix=0.5),
            Gain(gain_db=4),
        ])
    raise ValueError(f"Unknown effect: {effect}")


def apply_effect(audio_bytes: bytes, effect: str) -> bytes:
    """Apply a voice effect preset to raw WAV bytes and return processed WAV bytes.

    If effect is 'clean', returns the input unchanged.
    """
    effect = effect.lower().strip()
    if effect == "clean":
        return audio_bytes

    board = _build_board(effect)
    if board is None:
        return audio_bytes

    # Decode WAV via pydub
    seg = AudioSegment.from_file(io.BytesIO(audio_bytes), format="wav")
    sample_rate = seg.frame_rate
    samples = np.array(seg.get_array_of_samples(), dtype=np.float32)

    # Handle stereo
    channels = seg.channels
    if channels > 1:
        samples = samples.reshape((-1, channels))
    else:
        samples = samples.reshape((-1, 1))

    # Normalise to -1..1 range (pydub uses int16)
    samples = samples / 32768.0

    # Process through pedalboard (expects float32, shape = (samples, channels))
    processed = board(samples, sample_rate)

    # Clip and convert back to int16
    processed = np.clip(processed, -1.0, 1.0)
    processed_int = (processed * 32767).astype(np.int16)

    # Rebuild AudioSegment
    out_seg = AudioSegment(
        data=processed_int.tobytes(),
        sample_width=2,
        frame_rate=sample_rate,
        channels=channels,
    )

    buf = io.BytesIO()
    out_seg.export(buf, format="wav")
    return buf.getvalue()
