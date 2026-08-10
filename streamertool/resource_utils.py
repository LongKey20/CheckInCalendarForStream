from __future__ import annotations

import shutil
from pathlib import Path

from .constants import (
    AUDIO_DIR,
    BUNDLE_DIR,
    DEFAULT_AUDIO_FILE,
    DEFAULT_AUDIO_SOURCE_FILE,
    LEGACY_SOUND_DIR,
)


def default_audio_source_path() -> Path | None:
    candidates = [
        BUNDLE_DIR / "audio" / DEFAULT_AUDIO_SOURCE_FILE,
        AUDIO_DIR / DEFAULT_AUDIO_SOURCE_FILE,
        LEGACY_SOUND_DIR / DEFAULT_AUDIO_SOURCE_FILE,
    ]
    return next((path for path in candidates if path.is_file()), None)


def ensure_default_audio(force: bool = False) -> bool:
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    destination = AUDIO_DIR / DEFAULT_AUDIO_FILE
    if destination.is_file() and not force:
        return True
    source = default_audio_source_path()
    if source is None:
        return destination.is_file()
    try:
        if source.resolve() != destination.resolve():
            shutil.copy2(source, destination)
    except OSError:
        return destination.is_file()
    return destination.is_file()


def active_audio_path(file_name: str) -> Path | None:
    if not file_name:
        return None
    audio_name = Path(file_name).name
    audio_path = AUDIO_DIR / audio_name
    if audio_path.is_file():
        return audio_path
    legacy_path = LEGACY_SOUND_DIR / audio_name
    if legacy_path.is_file():
        return legacy_path
    return None
