from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

from .constants import (
    BUNDLE_DIR,
    CALENDAR_CSS_DIR,
    CALENDAR_CSS_FILE,
    CALENDAR_SIMPLE_FONT_SOURCE_CUSTOM,
    CALENDAR_THEME_DIR,
    CALENDAR_THEME_MODE_SIMPLE,
    CALL_CSS_DIR,
    CALL_CSS_FILE,
    CSS_VERSION,
    CSS_VERSION_MARKER_PREFIX,
    QUEUE_CSS_DIR,
    QUEUE_CSS_FILE,
)
from .default_css import DEFAULT_CSS
from .utils import css_string, hex_to_rgb, parse_aspect_ratio


def ensure_default_css() -> None:
    for directory in (CALL_CSS_DIR.parent, CALL_CSS_DIR, QUEUE_CSS_DIR, CALENDAR_CSS_DIR):
        directory.mkdir(parents=True, exist_ok=True)
    default_css_bytes = DEFAULT_CSS.encode("utf-8")
    bundled_calendar_css = BUNDLE_DIR / "css" / "calendar" / "default.css"
    if not CALENDAR_CSS_FILE.exists():
        calendar_css_bytes = bundled_calendar_css.read_bytes() if bundled_calendar_css.exists() else default_css_bytes
        CALENDAR_CSS_FILE.write_bytes(calendar_css_bytes)
    for target in (CALL_CSS_FILE, QUEUE_CSS_FILE):
        if not target.exists():
            target.write_bytes(default_css_bytes)


def css_version(path: Path) -> int | None:
    try:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines()[:12]:
            if CSS_VERSION_MARKER_PREFIX in line:
                value = line.split(CSS_VERSION_MARKER_PREFIX, 1)[1].strip(" */")
                return int(value)
    except (OSError, ValueError):
        return None
    return None


def selected_css_entries(state) -> list[tuple[str, Path]]:
    ensure_default_css()
    entries: list[tuple[str, Path]] = []
    area_map = {
        "call": (CALL_CSS_DIR, "call_css_file"),
        "queue": (QUEUE_CSS_DIR, "queue_css_file"),
        "calendar": (CALENDAR_CSS_DIR, "calendar_css_file"),
    }
    with state.lock:
        for area, (css_dir, state_attr) in area_map.items():
            if area == "calendar" and state.calendar_theme_mode == CALENDAR_THEME_MODE_SIMPLE:
                continue
            css_file = Path(getattr(state, state_attr, "default.css") or "default.css").name
            css_path = css_dir / css_file
            if css_path.is_file():
                entries.append((area, css_path))
    return entries


def outdated_selected_css_entries(state) -> list[tuple[str, Path, int | None]]:
    outdated: list[tuple[str, Path, int | None]] = []
    seen: set[Path] = set()
    for area, css_path in selected_css_entries(state):
        resolved = css_path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        version = css_version(css_path)
        if version is None or version < CSS_VERSION:
            outdated.append((area, css_path, version))
    return outdated


def css_version_marker() -> str:
    return f"/*\n * {CSS_VERSION_MARKER_PREFIX} {CSS_VERSION}\n */"


def migrate_css_content(content: str) -> str:
    lines = content.splitlines()
    for index, line in enumerate(lines[:12]):
        if CSS_VERSION_MARKER_PREFIX in line:
            lines[index] = f" * {CSS_VERSION_MARKER_PREFIX} {CSS_VERSION}"
            line_ending = "\n" if content.endswith("\n") else ""
            return "\n".join(lines) + line_ending
    separator = "" if not content else "\n\n"
    return f"{css_version_marker()}{separator}{content}"


def backup_and_migrate_css(_area: str, css_path: Path, version: int | None) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    old_version = str(version) if version is not None else "unknown"
    backup_dir = css_path.parent / "backup"
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_path = backup_dir / f"{css_path.stem}.backup-v{old_version}-{timestamp}{css_path.suffix}"
    shutil.copy2(css_path, backup_path)
    original = css_path.read_text(encoding="utf-8", errors="replace")
    css_path.write_text(migrate_css_content(original), encoding="utf-8")
    return backup_path


def active_css_path(state, area: str) -> Path:
    ensure_default_css()
    area_map = {
        "call": (CALL_CSS_DIR, "call_css_file", CALL_CSS_FILE),
        "queue": (QUEUE_CSS_DIR, "queue_css_file", QUEUE_CSS_FILE),
        "calendar": (CALENDAR_CSS_DIR, "calendar_css_file", CALENDAR_CSS_FILE),
    }
    css_dir, state_attr, default_path = area_map.get(area, area_map["call"])
    with state.lock:
        css_file = Path(getattr(state, state_attr, "default.css") or "default.css").name
        css_path = css_dir / css_file
        if not css_path.is_file():
            setattr(state, state_attr, "default.css")
            state.save()
            css_path = default_path
    return css_path


def bundled_calendar_css_text() -> str:
    for css_path in (
        BUNDLE_DIR / "css" / "calendar" / "default.css",
        CALENDAR_CSS_FILE,
    ):
        try:
            if css_path.is_file():
                return css_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
    return DEFAULT_CSS


def active_calendar_background_path(state) -> Path | None:
    with state.lock:
        image_name = Path(state.calendar_background_image or "").name
    if not image_name:
        return None
    image_path = CALENDAR_THEME_DIR / image_name
    if image_path.is_file():
        return image_path
    return None


def active_calendar_font_path(state) -> Path | None:
    with state.lock:
        font_source = state.calendar_simple_font_source
        font_name = Path(state.calendar_simple_font_file or "").name
    if font_source != CALENDAR_SIMPLE_FONT_SOURCE_CUSTOM:
        return None
    if not font_name:
        return None
    font_path = CALENDAR_THEME_DIR / font_name
    if font_path.is_file():
        return font_path
    return None


def calendar_css_response(state) -> bytes:
    with state.lock:
        simple_mode = state.calendar_theme_mode == CALENDAR_THEME_MODE_SIMPLE
    if not simple_mode:
        return active_css_path(state, "calendar").read_bytes()
    css = bundled_calendar_css_text()
    background_path = active_calendar_background_path(state)
    font_path = active_calendar_font_path(state)
    with state.lock:
        style_version = state.calendar_style_version
        aspect_ratio = state.calendar_simple_aspect_ratio
        font_family = state.calendar_simple_font_family
        text_color = state.calendar_simple_text_color
        day_bg_color = state.calendar_simple_day_bg_color
        day_bg_opacity = state.calendar_simple_day_bg_opacity
        today_border_color = state.calendar_simple_today_border_color
        first_glow_color = state.calendar_simple_first_glow_color
    day_bg_r, day_bg_g, day_bg_b = hex_to_rgb(day_bg_color)
    first_glow_r, first_glow_g, first_glow_b = hex_to_rgb(first_glow_color)
    aspect_width, aspect_height = parse_aspect_ratio(aspect_ratio)
    day_bg_alpha = max(0, min(100, day_bg_opacity)) / 100
    if font_path:
        css += f"""

/* StreamerTool Simple Calendar Custom Font */
@font-face {{
    font-family: "StreamerToolSimpleCustomFont";
    src: url("/calendar/simple-font?style={style_version}");
    font-display: swap;
}}
"""
        font_stack = f'"StreamerToolSimpleCustomFont", {css_string(font_family)}, sans-serif'
    else:
        font_stack = f"{css_string(font_family)}, sans-serif"
    css += f"""

/* StreamerTool Simple Calendar Theme */
:root {{
    --calendar-aspect-w: {aspect_width:g};
    --calendar-aspect-h: {aspect_height:g};
    --font-family: {font_stack};
    --text-color: {text_color};
    --day-name-color: {text_color};
    --alert-color: {text_color};
    --header-color: {text_color};
    --day-bg: rgba({day_bg_r}, {day_bg_g}, {day_bg_b}, {day_bg_alpha:.2f});
    --today-border-color: {today_border_color};
    --first-stamp-glow-color: {first_glow_color};
    --first-stamp-glow-soft-color: rgba({first_glow_r}, {first_glow_g}, {first_glow_b}, 0.55);
}}

.day.first-stamp-day::after {{
    box-shadow:
        0 0 var(--first-stamp-glow-small) var(--first-stamp-glow-color),
        0 0 var(--first-stamp-glow-medium) var(--first-stamp-glow-soft-color),
        0 0 var(--first-stamp-glow-large) rgba({first_glow_r}, {first_glow_g}, {first_glow_b}, 0.35) !important;
}}

.days-grid {{
    grid-template-rows: auto repeat(6, minmax(0, 1fr)) !important;
    align-content: stretch !important;
}}

.day,
.empty-day {{
    aspect-ratio: auto !important;
    height: 100% !important;
    min-height: 0 !important;
}}
"""
    if background_path:
        css += f"""

.calendar-container {{
    background: url("/calendar/simple-background?style={style_version}") center / cover no-repeat !important;
    background-image: url("/calendar/simple-background?style={style_version}") !important;
    background-position: center !important;
    background-size: cover !important;
    background-repeat: no-repeat !important;
}}
"""
    return css.encode("utf-8")
