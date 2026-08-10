from __future__ import annotations

import csv
import json
import os
import threading
import time
from datetime import datetime
from pathlib import Path

from .avatar_cache import AvatarCache
from .constants import *
from .i18n import TRANSLATIONS, default_calendar_texts, detect_default_language, normalize_weekday_language
from .resource_utils import active_audio_path, ensure_default_audio
from .time_utils import detect_default_time_zone_label, timezone_from_setting
from .utils import normalize_aspect_ratio, normalize_blacklist_name, normalize_hex_color

class State:
    def __init__(self) -> None:
        SETTING_DIR.mkdir(parents=True, exist_ok=True)
        CSS_DIR.mkdir(parents=True, exist_ok=True)
        CALL_CSS_DIR.mkdir(parents=True, exist_ok=True)
        QUEUE_CSS_DIR.mkdir(parents=True, exist_ok=True)
        CALENDAR_CSS_DIR.mkdir(parents=True, exist_ok=True)
        AUDIO_DIR.mkdir(parents=True, exist_ok=True)
        CALENDAR_THEME_DIR.mkdir(parents=True, exist_ok=True)
        AVATAR_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        TWITCH_AVATAR_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        CSV_DIR.mkdir(parents=True, exist_ok=True)
        ensure_default_audio()
        self.lock = threading.RLock()
        self.queue: list[str] = []
        self.channel = ""
        self.call_count = 1
        self.accept_queue = True
        self.display_text = "輪到{name}囉"
        self.port = PORT
        self.language = detect_default_language()
        self.display_seconds = 8
        self.queue_display_limit = 6
        self.queue_display_seconds = 8
        self.calendar_display_seconds = 6
        self.avatar_cache_days = 28
        self.calendar_time_zone = detect_default_time_zone_label()
        self.calendar_weekday_language = normalize_weekday_language(self.language, "zh")
        self.calendar_csv_prefix = ""
        calendar_texts = default_calendar_texts(self.language)
        self.calendar_first_text = calendar_texts["first"]
        self.calendar_checkin_text = calendar_texts["checkin"]
        self.calendar_command_text = calendar_texts["command"]
        self.sound_file = DEFAULT_AUDIO_FILE if (AUDIO_DIR / DEFAULT_AUDIO_FILE).is_file() else ""
        self.calendar_sound_file = DEFAULT_AUDIO_FILE if (AUDIO_DIR / DEFAULT_AUDIO_FILE).is_file() else ""
        self.sound_muted = False
        self.calendar_sound_muted = False
        self.known_users: dict[str, str] = {}
        self.css_file = "default.css"
        self.call_css_file = "default.css"
        self.queue_css_file = "default.css"
        self.calendar_css_file = "default.css"
        self.calendar_theme_mode = CALENDAR_THEME_MODE_CSS
        self.calendar_background_image = ""
        self.calendar_simple_aspect_ratio = "1:1"
        self.calendar_simple_font_source = CALENDAR_SIMPLE_FONT_SOURCE_PRESET
        self.calendar_simple_font_family = DEFAULT_SIMPLE_FONT_OPTIONS[0]
        self.calendar_simple_font_file = ""
        self.calendar_simple_text_color = "#ffffff"
        self.calendar_simple_day_bg_color = "#ffffff"
        self.calendar_simple_day_bg_opacity = 8
        self.calendar_simple_today_border_color = "#a970ff"
        self.calendar_simple_first_glow_color = "#ffd640"
        self.commands = list(DEFAULT_JOIN_COMMANDS)
        self.queue_commands = list(DEFAULT_QUEUE_COMMANDS)
        self.calendar_commands = list(DEFAULT_CALENDAR_COMMANDS)
        self.blacklist_names = list(DEFAULT_BLACKLIST_NAMES)
        self.avatar_cache = AvatarCache(lambda: self.avatar_cache_days)
        self.last_called_names: list[str] = []
        self.calendar_overlay_queue: list[dict] = []
        self.calendar_style_version = 1
        self.overlay_event = {
            "call": {
                "id": 0,
                "names": [],
                "text": "",
                "duration_ms": 8000,
                "sound_url": "",
                "visible": False,
                "created_at": 0,
            },
            "queue": {
                "id": 0,
                "items": [],
                "has_more": False,
                "duration_ms": 8000,
                "visible": False,
                "created_at": 0,
            },
            "calendar": {
                "id": 0,
                "year": 0,
                "month": 0,
                "today": 0,
                "username": "",
                "display_name": "",
                "message": "",
                "dates": [],
                "signed_date": "",
                "avatar_url": "",
                "duration_ms": 6000,
                "sound_url": "",
                "weekday_language": "zh",
                "visible": False,
                "created_at": 0,
            },
        }
        self.load()
        self.load_commands()
        self.save()
        self.save_commands()

    def load(self) -> None:
        try:
            source = STATE_FILE
            if not source.exists():
                source = next((path for path in LEGACY_STATE_FILES if path.exists()), source)
            data = json.loads(source.read_text(encoding="utf-8"))
            self.queue = [str(name) for name in data.get("queue", [])]
            self.channel = str(data.get("channel", "")).lstrip("#").lower()
            self.call_count = max(1, int(data.get("call_count", 1)))
            self.accept_queue = bool(data.get("accept_queue", True))
            self.display_text = str(data.get("display_text", "輪到{name}囉"))
            self.port = min(65535, max(1024, int(data.get("port", PORT))))
            language = str(data.get("language", detect_default_language()))
            self.language = language if language in TRANSLATIONS else "en"
            calendar_texts = default_calendar_texts(self.language)
            self.display_seconds = min(300, max(0, int(data.get("display_seconds", 8))))
            self.queue_display_limit = min(100, max(1, int(data.get("queue_display_limit", 6))))
            self.queue_display_seconds = min(300, max(0, int(data.get("queue_display_seconds", 8))))
            self.calendar_display_seconds = min(300, max(0, int(data.get("calendar_display_seconds", 6))))
            self.avatar_cache_days = min(365, max(0, int(data.get("avatar_cache_days", 28))))
            stored_time_zone = str(data.get("calendar_time_zone", detect_default_time_zone_label())).strip()
            if stored_time_zone.casefold() == SYSTEM_TIME_ZONE_LABEL.casefold():
                stored_time_zone = detect_default_time_zone_label()
            self.calendar_time_zone = stored_time_zone or detect_default_time_zone_label()
            self.calendar_weekday_language = normalize_weekday_language(
                str(data.get("calendar_weekday_language", self.language)),
                normalize_weekday_language(self.language, "zh"),
            )
            self.calendar_csv_prefix = str(data.get("calendar_csv_prefix", ""))
            self.calendar_first_text = str(data.get("calendar_first_text", calendar_texts["first"]))
            self.calendar_checkin_text = str(data.get("calendar_checkin_text", calendar_texts["checkin"]))
            self.calendar_command_text = str(data.get("calendar_command_text", calendar_texts["command"]))
            sound_file = Path(str(data.get("sound_file", ""))).name
            self.sound_file = sound_file if sound_file else ""
            calendar_sound_file = Path(str(data.get("calendar_sound_file", ""))).name
            self.calendar_sound_file = calendar_sound_file if calendar_sound_file else ""
            if not self.sound_file and (AUDIO_DIR / DEFAULT_AUDIO_FILE).is_file():
                self.sound_file = DEFAULT_AUDIO_FILE
            if not self.calendar_sound_file and (AUDIO_DIR / DEFAULT_AUDIO_FILE).is_file():
                self.calendar_sound_file = DEFAULT_AUDIO_FILE
            self.sound_muted = bool(data.get("sound_muted", False))
            self.calendar_sound_muted = bool(data.get("calendar_sound_muted", False))
            css_file = Path(str(data.get("css_file", "default.css"))).name
            self.css_file = css_file if css_file else "default.css"
            self.call_css_file = Path(str(data.get("call_css_file", self.css_file))).name or "default.css"
            self.queue_css_file = Path(str(data.get("queue_css_file", self.css_file))).name or "default.css"
            self.calendar_css_file = Path(str(data.get("calendar_css_file", self.css_file))).name or "default.css"
            calendar_theme_mode = str(data.get("calendar_theme_mode", CALENDAR_THEME_MODE_CSS)).strip()
            self.calendar_theme_mode = (
                CALENDAR_THEME_MODE_SIMPLE
                if calendar_theme_mode == CALENDAR_THEME_MODE_SIMPLE
                else CALENDAR_THEME_MODE_CSS
            )
            self.calendar_background_image = Path(str(data.get("calendar_background_image", ""))).name
            self.calendar_simple_aspect_ratio = normalize_aspect_ratio(
                str(data.get("calendar_simple_aspect_ratio", "1:1")),
                "1:1",
            )
            self.calendar_simple_font_family = str(
                data.get("calendar_simple_font_family", DEFAULT_SIMPLE_FONT_OPTIONS[0])
            ).strip() or DEFAULT_SIMPLE_FONT_OPTIONS[0]
            self.calendar_simple_font_file = Path(str(data.get("calendar_simple_font_file", ""))).name
            calendar_simple_font_source = str(data.get("calendar_simple_font_source", "")).strip()
            if calendar_simple_font_source in {
                CALENDAR_SIMPLE_FONT_SOURCE_PRESET,
                CALENDAR_SIMPLE_FONT_SOURCE_CUSTOM,
            }:
                self.calendar_simple_font_source = calendar_simple_font_source
            else:
                self.calendar_simple_font_source = (
                    CALENDAR_SIMPLE_FONT_SOURCE_CUSTOM
                    if self.calendar_simple_font_file
                    else CALENDAR_SIMPLE_FONT_SOURCE_PRESET
                )
            self.calendar_simple_text_color = normalize_hex_color(
                str(data.get("calendar_simple_text_color", "#ffffff")),
                "#ffffff",
            )
            self.calendar_simple_day_bg_color = normalize_hex_color(
                str(data.get("calendar_simple_day_bg_color", "#ffffff")),
                "#ffffff",
            )
            self.calendar_simple_day_bg_opacity = min(
                100,
                max(0, int(data.get("calendar_simple_day_bg_opacity", 8))),
            )
            self.calendar_simple_today_border_color = normalize_hex_color(
                str(data.get("calendar_simple_today_border_color", "#a970ff")),
                "#a970ff",
            )
            self.calendar_simple_first_glow_color = normalize_hex_color(
                str(data.get("calendar_simple_first_glow_color", "#ffd640")),
                "#ffd640",
            )
            called = data.get("last_called_names", [])
            if isinstance(called, list):
                self.last_called_names = [str(name) for name in called]
            blacklist_names = data.get("blacklist_names", None)
            if isinstance(blacklist_names, list):
                cleaned = [str(name).strip().lstrip("@") for name in blacklist_names if normalize_blacklist_name(str(name))]
                self.blacklist_names = list(dict.fromkeys(cleaned))
            elif blacklist_names is None:
                existing_blacklist = {normalize_blacklist_name(name) for name in self.blacklist_names}
                self.blacklist_names.extend(
                    name for name in DEFAULT_BLACKLIST_NAMES if normalize_blacklist_name(name) not in existing_blacklist
                )
        except (FileNotFoundError, ValueError, TypeError, json.JSONDecodeError):
            pass

    def load_commands(self) -> None:
        try:
            source = COMMAND_FILE if COMMAND_FILE.exists() else LEGACY_COMMAND_FILE
            data = json.loads(source.read_text(encoding="utf-8"))
            join_commands = data.get("join_commands", data.get("commands", []))
            if isinstance(join_commands, list):
                cleaned = [str(command).strip() for command in join_commands if str(command).strip()]
                self.commands = list(dict.fromkeys(cleaned))
            queue_commands = data.get("queue_commands", [])
            if isinstance(queue_commands, list):
                cleaned = [str(command).strip() for command in queue_commands if str(command).strip()]
                self.queue_commands = list(dict.fromkeys(cleaned))
            calendar_commands = data.get("calendar_commands", [])
            if isinstance(calendar_commands, list):
                cleaned = [str(command).strip() for command in calendar_commands if str(command).strip()]
                self.calendar_commands = list(dict.fromkeys(cleaned))
            if int(data.get("config_version", 1)) < COMMAND_CONFIG_VERSION:
                existing = {command.casefold() for command in self.commands}
                self.commands.extend(
                    command for command in DEFAULT_JOIN_COMMANDS if command.casefold() not in existing
                )
                existing = {command.casefold() for command in self.queue_commands}
                self.queue_commands.extend(
                    command for command in DEFAULT_QUEUE_COMMANDS if command.casefold() not in existing
                )
                existing = {command.casefold() for command in self.calendar_commands}
                self.calendar_commands.extend(
                    command for command in DEFAULT_CALENDAR_COMMANDS if command.casefold() not in existing
                )
        except (FileNotFoundError, ValueError, TypeError, json.JSONDecodeError):
            pass

    def save(self) -> None:
        with self.lock:
            payload = {
                "queue": self.queue,
                "channel": self.channel,
                "call_count": self.call_count,
                "accept_queue": self.accept_queue,
                "display_text": self.display_text,
                "port": self.port,
                "language": self.language,
                "display_seconds": self.display_seconds,
                "queue_display_limit": self.queue_display_limit,
                "queue_display_seconds": self.queue_display_seconds,
                "calendar_display_seconds": self.calendar_display_seconds,
                "avatar_cache_days": self.avatar_cache_days,
                "calendar_time_zone": self.calendar_time_zone,
                "calendar_weekday_language": self.calendar_weekday_language,
                "calendar_csv_prefix": self.calendar_csv_prefix,
                "calendar_first_text": self.calendar_first_text,
                "calendar_checkin_text": self.calendar_checkin_text,
                "calendar_command_text": self.calendar_command_text,
                "sound_file": self.sound_file,
                "calendar_sound_file": self.calendar_sound_file,
                "sound_muted": self.sound_muted,
                "calendar_sound_muted": self.calendar_sound_muted,
                "css_file": self.css_file,
                "call_css_file": self.call_css_file,
                "queue_css_file": self.queue_css_file,
                "calendar_css_file": self.calendar_css_file,
                "calendar_theme_mode": self.calendar_theme_mode,
                "calendar_background_image": self.calendar_background_image,
                "calendar_simple_aspect_ratio": self.calendar_simple_aspect_ratio,
                "calendar_simple_font_source": self.calendar_simple_font_source,
                "calendar_simple_font_family": self.calendar_simple_font_family,
                "calendar_simple_font_file": self.calendar_simple_font_file,
                "calendar_simple_text_color": self.calendar_simple_text_color,
                "calendar_simple_day_bg_color": self.calendar_simple_day_bg_color,
                "calendar_simple_day_bg_opacity": self.calendar_simple_day_bg_opacity,
                "calendar_simple_today_border_color": self.calendar_simple_today_border_color,
                "calendar_simple_first_glow_color": self.calendar_simple_first_glow_color,
                "blacklist_names": self.blacklist_names,
                "last_called_names": self.last_called_names,
            }
            temp = STATE_FILE.with_suffix(".tmp")
            temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            os.replace(temp, STATE_FILE)

    def save_commands(self) -> None:
        with self.lock:
            payload = {
                "config_version": COMMAND_CONFIG_VERSION,
                "join_commands": self.commands,
                "queue_commands": self.queue_commands,
                "calendar_commands": self.calendar_commands,
            }
            temp = COMMAND_FILE.with_suffix(".tmp")
            temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            os.replace(temp, COMMAND_FILE)

    def is_blacklisted(self, login: str, display_name: str = "") -> bool:
        candidates = {normalize_blacklist_name(login), normalize_blacklist_name(display_name)}
        candidates.discard("")
        if not candidates:
            return False
        blacklist = {normalize_blacklist_name(name) for name in self.blacklist_names}
        return bool(candidates & blacklist)

    def touch_calendar_style(self) -> None:
        self.calendar_style_version += 1

    def add_viewer(self, name: str) -> bool:
        with self.lock:
            if not self.accept_queue:
                return False
            if name.casefold() in (item.casefold() for item in self.queue):
                return False
            self.queue.append(name)
            self.refresh_queue_overlay()
            self.save()
            return True

    def _queue_overlay_payload(self) -> tuple[list[str], bool]:
        limit = max(1, self.queue_display_limit)
        items = self.queue[:limit]
        return items, len(self.queue) > limit

    def refresh_queue_overlay(self) -> None:
        self.expire_overlays()
        queue_overlay = self.overlay_event["queue"]
        if not queue_overlay.get("visible"):
            return
        items, has_more = self._queue_overlay_payload()
        queue_overlay.update(
            {
                "id": queue_overlay["id"] + 1,
                "items": items,
                "has_more": has_more,
                "duration_ms": self.queue_display_seconds * 1000,
                "created_at": time.time(),
            }
        )

    def show_queue_overlay(self) -> None:
        with self.lock:
            items, has_more = self._queue_overlay_payload()
            queue_overlay = self.overlay_event["queue"]
            queue_overlay.update(
                {
                    "id": queue_overlay["id"] + 1,
                    "items": items,
                    "has_more": has_more,
                    "duration_ms": self.queue_display_seconds * 1000,
                    "visible": True,
                    "created_at": time.time(),
                }
            )

    def hide_queue_overlay(self) -> None:
        with self.lock:
            queue_overlay = self.overlay_event["queue"]
            queue_overlay.update(
                {
                    "id": queue_overlay["id"] + 1,
                    "visible": False,
                    "created_at": time.time(),
                }
            )

    def is_queue_overlay_visible(self) -> bool:
        self.expire_overlays()
        with self.lock:
            return bool(self.overlay_event["queue"].get("visible"))

    def _show_call_overlay(self, names: list[str]) -> None:
        sound_path = None if self.sound_muted else active_audio_path(self.sound_file)
        call_overlay = self.overlay_event["call"]
        call_overlay.update(
            {
                "id": call_overlay["id"] + 1,
                "names": names,
                "text": self.display_text.replace("{name}", ", ".join(names)),
                "duration_ms": self.display_seconds * 1000,
                "sound_url": "/audio/call" if sound_path and sound_path.is_file() else "",
                "visible": True,
                "created_at": time.time(),
            }
        )

    def hide_call_overlay(self) -> None:
        with self.lock:
            call_overlay = self.overlay_event["call"]
            call_overlay.update(
                {
                    "id": call_overlay["id"] + 1,
                    "visible": False,
                    "sound_url": "",
                    "created_at": time.time(),
                }
            )

    def expire_overlays(self) -> None:
        with self.lock:
            now = time.time()
            for overlay in (self.overlay_event["call"], self.overlay_event["queue"]):
                duration_ms = int(overlay.get("duration_ms", 0) or 0)
                created_at = float(overlay.get("created_at", 0) or 0)
                if overlay.get("visible") and duration_ms > 0 and created_at and now - created_at >= duration_ms / 1000:
                    overlay.update(
                        {
                            "id": overlay["id"] + 1,
                            "visible": False,
                            "sound_url": "",
                            "created_at": now,
                        }
                    )
            calendar_overlay = self.overlay_event["calendar"]
            calendar_duration_ms = int(calendar_overlay.get("duration_ms", 0) or 0)
            calendar_created_at = float(calendar_overlay.get("created_at", 0) or 0)
            if (
                calendar_overlay.get("visible")
                and calendar_duration_ms > 0
                and calendar_created_at
                and now - calendar_created_at >= calendar_duration_ms / 1000
            ):
                if not self._show_next_calendar_overlay():
                    calendar_overlay.update(
                        {
                            "id": calendar_overlay["id"] + 1,
                            "visible": False,
                            "sound_url": "",
                            "created_at": now,
                        }
                    )
            self.refresh_visible_calendar_date()

    def refresh_visible_calendar_date(self) -> None:
        calendar_overlay = self.overlay_event["calendar"]
        if not calendar_overlay.get("visible"):
            return
        if int(calendar_overlay.get("today", 0) or 0) <= 0:
            return
        username = str(calendar_overlay.get("username", "") or "").strip()
        if not username:
            return
        now = self.calendar_now()
        if (
            int(calendar_overlay.get("year", 0) or 0) == now.year
            and int(calendar_overlay.get("month", 0) or 0) == now.month
            and int(calendar_overlay.get("today", 0) or 0) == now.day
        ):
            return
        rows = self.read_calendar_rows(now.year, now.month)
        user_dates = [
            {"date": row["date"], "isFirst": row.get("isFirst", "").upper() == "YES"}
            for row in rows
            if row.get("username", "").casefold() == username.casefold()
        ]
        calendar_overlay.update(
            {
                "id": calendar_overlay["id"] + 1,
                "year": now.year,
                "month": now.month,
                "today": now.day,
                "dates": user_dates,
                "signed_date": "",
                "sound_url": "",
            }
        )

    def replay_last_call(self) -> bool:
        with self.lock:
            if not self.last_called_names:
                return False
            self._show_call_overlay(self.last_called_names)
            return True

    def call_next(self, count: int) -> list[str]:
        with self.lock:
            names = self.queue[:count]
            if not names:
                return []
            del self.queue[:count]
            self.last_called_names = names
            self._show_call_overlay(names)
            self.refresh_queue_overlay()
            self.save()
            return names

    def calendar_now(self) -> datetime:
        return datetime.now(timezone_from_setting(self.calendar_time_zone))

    @staticmethod
    def render_calendar_text(template: str, name: str) -> str:
        text = str(template or "").strip()
        return (text or "{name}").replace("{name}", name)

    def _activate_calendar_overlay(self, payload: dict) -> None:
        calendar_overlay = self.overlay_event["calendar"]
        next_payload = dict(payload)
        next_payload.update(
            {
                "id": calendar_overlay["id"] + 1,
                "visible": True,
                "created_at": time.time(),
            }
        )
        calendar_overlay.update(next_payload)

    def _show_next_calendar_overlay(self) -> bool:
        if not self.calendar_overlay_queue:
            return False
        self._activate_calendar_overlay(self.calendar_overlay_queue.pop(0))
        return True

    def _show_or_queue_calendar_overlay(self, payload: dict) -> None:
        calendar_overlay = self.overlay_event["calendar"]
        duration_ms = int(payload.get("duration_ms", 0) or 0)
        current_duration_ms = int(calendar_overlay.get("duration_ms", 0) or 0)
        if calendar_overlay.get("visible") and current_duration_ms > 0 and duration_ms > 0:
            self.calendar_overlay_queue.append(dict(payload))
            return
        if duration_ms <= 0:
            self.calendar_overlay_queue.clear()
        self._activate_calendar_overlay(payload)

    def calendar_csv_path(self, year: int, month: int) -> Path:
        return CSV_DIR / f"{self.calendar_csv_prefix}{year}-{month:02d}.csv"

    def read_calendar_rows(self, year: int, month: int) -> list[dict[str, str]]:
        path = self.calendar_csv_path(year, month)
        if not path.exists() or path.stat().st_size <= 0:
            return []
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            return [
                {key: str(row.get(key, "") or "") for key in CALENDAR_HEADERS}
                for row in reader
                if row.get("date") and row.get("username")
            ]

    def write_calendar_rows(self, year: int, month: int, rows: list[dict[str, str]]) -> None:
        CSV_DIR.mkdir(parents=True, exist_ok=True)
        path = self.calendar_csv_path(year, month)
        temp = path.with_suffix(".tmp")
        with temp.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=CALENDAR_HEADERS)
            writer.writeheader()
            writer.writerows(rows)
        os.replace(temp, path)

    def remember_user(self, username: str, display_name: str = "") -> None:
        username = str(username or "").strip().lstrip("@").lower()
        if not username:
            return
        display_name = str(display_name or "").strip() or username
        with self.lock:
            self.known_users[username] = display_name

    def resolve_calendar_identity(
        self,
        target: str,
        date_override: tuple[int, int] | None = None,
    ) -> tuple[str, str]:
        target = str(target or "").strip().lstrip("@")
        if not target:
            return "", ""
        folded = target.casefold()
        with self.lock:
            known_users = dict(self.known_users)
        for username, display_name in known_users.items():
            if folded in (username.casefold(), display_name.casefold()):
                return username, display_name

        now = self.calendar_now()
        months = [date_override if date_override else (now.year, now.month)]
        if date_override:
            months.append((now.year, now.month))
        seen_months = set()
        for month_info in months:
            if month_info in seen_months:
                continue
            seen_months.add(month_info)
            rows = self.read_calendar_rows(*month_info)
            for row in reversed(rows):
                username = row.get("username", "").strip()
                display_name = row.get("displayName", "").strip() or username
                if folded in (username.casefold(), display_name.casefold()):
                    self.remember_user(username, display_name)
                    return username, display_name
        return target.lower(), target

    def show_calendar(
        self,
        username: str,
        display_name: str,
        date_override: tuple[int, int] | None = None,
        command_only: bool = False,
    ) -> bool:
        self.remember_user(username, display_name)
        avatar_url = self.avatar_cache.prepare(username)
        with self.lock:
            now = self.calendar_now()
            year, month = date_override if date_override else (now.year, now.month)
            today = 0 if date_override else now.day
            date_key = f"{year}-{month:02d}-{today:02d}" if today else ""
            rows = self.read_calendar_rows(year, month)
            user_dates = [
                {"date": row["date"], "isFirst": row.get("isFirst", "").upper() == "YES"}
                for row in rows
                if row.get("username", "").casefold() == username.casefold()
            ]
            already_today = bool(date_key) and any(
                row.get("date") == date_key and row.get("username", "").casefold() == username.casefold()
                for row in rows
            )
            if already_today and not command_only:
                return False
            if date_key and not command_only:
                is_first = not any(row.get("date") == date_key for row in rows)
                rows.append(
                    {
                        "date": date_key,
                        "username": username,
                        "displayName": display_name,
                        "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
                        "isFirst": "YES" if is_first else "NO",
                    }
                )
                self.write_calendar_rows(year, month, rows)
                user_dates.append({"date": date_key, "isFirst": is_first})
                template = self.calendar_first_text if is_first else self.calendar_checkin_text
                message = self.render_calendar_text(template, display_name)
                signed_date = date_key
            elif date_override:
                message = self.render_calendar_text(self.calendar_command_text, display_name)
                signed_date = ""
            else:
                message = self.render_calendar_text(self.calendar_command_text, display_name)
                signed_date = ""
            calendar_sound_path = (
                active_audio_path(self.calendar_sound_file)
                if signed_date and not self.calendar_sound_muted
                else None
            )
            self._show_or_queue_calendar_overlay(
                {
                    "year": year,
                    "month": month,
                    "today": today,
                    "username": username,
                    "display_name": display_name,
                    "message": message,
                    "dates": user_dates,
                    "signed_date": signed_date,
                    "avatar_url": avatar_url,
                    "duration_ms": self.calendar_display_seconds * 1000,
                    "sound_url": "/audio/calendar" if calendar_sound_path else "",
                    "weekday_language": self.calendar_weekday_language,
                }
            )
            return True


