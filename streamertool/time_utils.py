from __future__ import annotations

from datetime import datetime, timedelta, timezone

from .constants import OTHER_TIME_ZONE_LABEL, UTC_TIME_ZONE_OPTIONS


def format_utc_offset(total_minutes: int) -> str:
    sign = "+" if total_minutes >= 0 else "-"
    total_minutes = abs(total_minutes)
    hours, minutes = divmod(total_minutes, 60)
    suffix = f"{hours}" if minutes == 0 else f"{hours}:{minutes:02d}"
    return f"UTC{sign}{suffix}"


def parse_utc_offset(value: str) -> int | None:
    text = str(value or "").strip()
    if not text:
        return None
    if text in UTC_TIME_ZONE_OPTIONS:
        return UTC_TIME_ZONE_OPTIONS[text]
    if text.casefold() in {OTHER_TIME_ZONE_LABEL.casefold(), "other", "?嗡?"}:
        return None
    normalized = text.upper()
    if normalized.startswith("UTC"):
        normalized = normalized[3:].strip()
    if normalized in {"", "Z"}:
        return 0
    sign = 1
    if normalized[0] == "+":
        normalized = normalized[1:]
    elif normalized[0] == "-":
        sign = -1
        normalized = normalized[1:]
    normalized = normalized.strip()
    if not normalized:
        return None
    parts = normalized.split(":", 1)
    try:
        hours = int(parts[0])
        minutes = int(parts[1]) if len(parts) == 2 else 0
    except ValueError:
        return None
    if hours > 14 or minutes < 0 or minutes >= 60:
        return None
    return sign * (hours * 60 + minutes)


def detect_default_time_zone_label() -> str:
    offset = datetime.now().astimezone().utcoffset() or timedelta()
    total_minutes = round(offset.total_seconds() / 60)
    for label, minutes in UTC_TIME_ZONE_OPTIONS.items():
        if minutes == total_minutes:
            return label
    return format_utc_offset(total_minutes)


def timezone_from_setting(value: str) -> timezone:
    minutes = parse_utc_offset(value)
    if minutes is None:
        minutes = parse_utc_offset(detect_default_time_zone_label()) or 0
    return timezone(timedelta(minutes=minutes), format_utc_offset(minutes))
