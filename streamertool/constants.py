from __future__ import annotations

import sys
from pathlib import Path


APP_DIR = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent.parent
BUNDLE_DIR = Path(getattr(sys, "_MEIPASS", APP_DIR))
SETTING_DIR = APP_DIR / "setting"
CSS_DIR = APP_DIR / "css"
CALL_CSS_DIR = CSS_DIR / "call"
QUEUE_CSS_DIR = CSS_DIR / "queue"
CALENDAR_CSS_DIR = CSS_DIR / "calendar"
AUDIO_DIR = APP_DIR / "audio"
LEGACY_SOUND_DIR = APP_DIR / "sound"
CALENDAR_THEME_DIR = SETTING_DIR / "calendar-theme"
AVATAR_CACHE_DIR = SETTING_DIR / "avatar-cache"
TWITCH_AVATAR_CACHE_DIR = AVATAR_CACHE_DIR / "twitch"
AVATAR_CACHE_META_FILE = TWITCH_AVATAR_CACHE_DIR / "metadata.json"
LEGACY_AVATAR_CACHE_META_FILE = SETTING_DIR / "avatar-cache.json"
DEFAULT_AUDIO_FILE = "default.mp3"
DEFAULT_AUDIO_SOURCE_FILE = "default.mp3"
CSV_DIR = APP_DIR / "csv"
STATE_FILE = SETTING_DIR / "setting.json"
COMMAND_FILE = SETTING_DIR / "command.json"
LEGACY_STATE_FILES = [APP_DIR / "queue-state.json", APP_DIR / "queue_state.json"]
LEGACY_COMMAND_FILE = APP_DIR / "command.json"
HAS_EXISTING_STATE_FILE = STATE_FILE.exists() or any(path.exists() for path in LEGACY_STATE_FILES)
CALL_CSS_FILE = CALL_CSS_DIR / "default.css"
QUEUE_CSS_FILE = QUEUE_CSS_DIR / "default.css"
CALENDAR_CSS_FILE = CALENDAR_CSS_DIR / "default.css"
HOST = "127.0.0.1"
PORT = 18080
APP_VERSION = "2.1.0"
LOG_MAX_LINES = 500
CHAT_IDLE_TIMEOUT_SECONDS = 610
AVATAR_CACHE_TTL_SECONDS = 28 * 24 * 60 * 60
AVATAR_CACHE_REQUEST_TIMEOUT_SECONDS = 2
CSS_VERSION = 1
CSS_VERSION_MARKER_PREFIX = "StreamerTool CSS Version:"
CALENDAR_THEME_MODE_CSS = "css"
CALENDAR_THEME_MODE_SIMPLE = "simple"
CALENDAR_SIMPLE_FONT_SOURCE_PRESET = "preset"
CALENDAR_SIMPLE_FONT_SOURCE_CUSTOM = "custom"
DEFAULT_SIMPLE_FONT_OPTIONS = [
    "Microsoft JhengHei",
    "Microsoft YaHei",
    "Meiryo",
    "Yu Gothic",
    "Malgun Gothic",
    "Arial",
    "Segoe UI",
    "Noto Sans CJK TC",
    "Noto Sans JP",
    "Noto Sans KR",
]
DEFAULT_SIMPLE_ASPECT_RATIO_OPTIONS = ["1:1", "4:3", "3:4", "16:9", "9:16", "21:9"]
DEFAULT_JOIN_COMMANDS = ["!排隊", "!join", "!queue", "!参加"]
DEFAULT_QUEUE_COMMANDS = ["!隊列", "!list", "!queue-list", "!キュー"]
DEFAULT_CALENDAR_COMMANDS = ["!月曆", "!calendar", "!カレンダー"]
DEFAULT_BLACKLIST_NAMES = [
    "Nightbot",
    "Streamlabs",
    "StreamElements",
    "Moobot",
    "Fossabot",
    "WizeBot",
    "Botisimo",
    "OWN3D",
    "Sery_Bot",
    "SoundAlerts",
    "PretzelRocks",
    "ChiwaBots",
]
STREAMING_TOOL_PROCESSES = {
    "obs64.exe": "OBS Studio",
    "obs32.exe": "OBS Studio",
    "streamlabs desktop.exe": "Streamlabs Desktop",
    "streamlabs obs.exe": "Streamlabs OBS",
    "twitchstudio.exe": "Twitch Studio",
}
COMMAND_CONFIG_VERSION = 5
CALENDAR_HEADERS = ["date", "username", "displayName", "timestamp", "isFirst"]
SYSTEM_TIME_ZONE_LABEL = "System Time Zone"
OTHER_TIME_ZONE_LABEL = "Other / Custom"
UTC_TIME_ZONE_OPTIONS = {
    "UTC+8 - Taiwan / China / Hong Kong / Singapore": 8 * 60,
    "UTC+9 - Japan / Korea": 9 * 60,
    "UTC+0 - UTC / United Kingdom": 0,
    "UTC-5 - US Eastern Standard": -5 * 60,
    "UTC-4 - US Eastern Daylight": -4 * 60,
    "UTC-8 - US Pacific Standard": -8 * 60,
    "UTC-7 - US Pacific Daylight": -7 * 60,
}
