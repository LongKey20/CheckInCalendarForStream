from __future__ import annotations

import base64
import csv
import hashlib
import json
import locale
import mimetypes
import os
import queue
import secrets
import shutil
import socket
import ssl
import struct
import subprocess
import sys
import threading
import time
import tkinter as tk
import webbrowser
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from urllib.parse import urlparse


APP_DIR = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
BUNDLE_DIR = Path(getattr(sys, "_MEIPASS", APP_DIR))
SETTING_DIR = APP_DIR / "setting"
CSS_DIR = APP_DIR / "css"
CALL_CSS_DIR = CSS_DIR / "call"
QUEUE_CSS_DIR = CSS_DIR / "queue"
CALENDAR_CSS_DIR = CSS_DIR / "calendar"
AUDIO_DIR = APP_DIR / "audio"
LEGACY_SOUND_DIR = APP_DIR / "sound"
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
APP_VERSION = "2.0.3"
LOG_MAX_LINES = 500
CHAT_IDLE_TIMEOUT_SECONDS = 420
CSS_VERSION = 1
CSS_VERSION_MARKER_PREFIX = "StreamerTool CSS Version:"
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
DEFAULT_CSS = """/*
 * StreamerTool CSS Version: 1
 * Queue for Streamer - OBS 憿舐內璅??
 * ?航?曹耨?寞迨瑼BS ??渡? Browser Source 敺?憟?唳見撘?
 */

html,
body {
  margin: 0;
  width: 100%;
  height: 100%;
  overflow: hidden;
  background: transparent;
}

body {
  --overlay-safe-padding: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: "Microsoft JhengHei", sans-serif;
}

#overlay-container {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.overlay-area {
  width: 100%;
  min-width: 0;
  height: 100%;
  display: flex;
  align-items: flex-start;
  justify-content: flex-start;
  padding: var(--overlay-safe-padding);
  box-sizing: border-box;
}

.overlay-message {
  max-width: 90%;
  box-sizing: border-box;
  padding: 26px 44px;
  color: white;
  font-size: 60px;
  font-weight: 900;
  text-align: center;
  white-space: normal;
  overflow-wrap: anywhere;
  word-break: break-word;
  -webkit-text-stroke: 2px #000;
  paint-order: stroke fill;
  text-shadow:
    3px 3px 0 #000,
    -3px 3px 0 #000,
    3px -3px 0 #000,
    -3px -3px 0 #000,
    0 4px 12px #000;
  background: transparent;
  border: 3px solid transparent;
  border-radius: 24px;
  box-shadow: none;
  opacity: 0;
  transform: translateY(28px) scale(0.92);
}

.overlay-message[hidden] {
  display: none;
}

.overlay-message.show {
  opacity: 1;
  animation: message-pop-in 0.32s cubic-bezier(0.2, 0.85, 0.3, 1.2) both;
}

/*
 * 瘥?靘?頝唾絲???啣?雿?
 * 0.055s ?臬???銋?????0.7s ?舀??????恍摨艾?
 */
#call-message .char {
  display: inline-block;
  white-space: pre;
}

#call-message.show .char {
  animation: character-bounce 0.78s cubic-bezier(0.2, 0.75, 0.35, 1) both;
  animation-delay: calc(var(--char-index) * 0.055s);
}

#queue-message {
  font-size: 46px;
  text-align: left;
}

#call-message {
  text-align: left;
}

.queue-list {
  margin: 0;
  padding-left: 1.6em;
}

.queue-list li {
  margin: 0.18em 0;
}

#queue-message.show .queue-list li {
  animation: queue-line-pop 0.46s cubic-bezier(0.2, 0.85, 0.3, 1.15) both;
}

#queue-message.show .queue-list li:nth-child(1) { animation-delay: 0.00s; }
#queue-message.show .queue-list li:nth-child(2) { animation-delay: 0.06s; }
#queue-message.show .queue-list li:nth-child(3) { animation-delay: 0.12s; }
#queue-message.show .queue-list li:nth-child(4) { animation-delay: 0.18s; }
#queue-message.show .queue-list li:nth-child(5) { animation-delay: 0.24s; }
#queue-message.show .queue-list li:nth-child(6) { animation-delay: 0.30s; }
#queue-message.show .queue-list li:nth-child(n + 7) { animation-delay: 0.36s; }

.queue-more {
  list-style-position: outside;
}

@keyframes message-pop-in {
  0% {
    opacity: 0;
    transform: translateY(28px) scale(0.92);
  }
  100% {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

@keyframes queue-line-pop {
  0% {
    opacity: 0;
    transform: translateX(-18px) scale(0.96);
  }
  100% {
    opacity: 1;
    transform: translateX(0) scale(1);
  }
}

@keyframes character-bounce {
  0% {
    transform: translateY(0) scale(1);
  }
  35% {
    transform: translateY(-22px) scale(1.08);
  }
  62% {
    transform: translateY(4px) scale(0.98);
  }
  78% {
    transform: translateY(-2px) scale(1.01);
  }
  100% {
    transform: translateY(0) scale(1);
  }
}
"""

LANGUAGES = {"中文": "zh", "English": "en", "日本語": "ja"}
LANGUAGE_NAMES = {code: name for name, code in LANGUAGES.items()}
WEEKDAY_LANGUAGE_OPTIONS = {"中": "zh", "英": "en", "日": "ja"}
WEEKDAY_LANGUAGE_NAMES = {code: name for name, code in WEEKDAY_LANGUAGE_OPTIONS.items()}


def normalize_weekday_language(value: str, fallback: str = "zh") -> str:
    language = str(value or "").strip()
    if language in WEEKDAY_LANGUAGE_OPTIONS:
        language = WEEKDAY_LANGUAGE_OPTIONS[language]
    return language if language in WEEKDAY_LANGUAGE_NAMES else fallback

TRANSLATIONS = {
    "zh": {
        "app_title": "StreamerTool",
        "queue_tab": "隊列管理",
        "settings_tab": "設定",
        "connection_log_tab": "連接和 Log",
        "command_settings_tab": "指令設定",
        "blacklist_tab": "黑名單",
        "queue_settings_tab": "隊列設定",
        "log": "Log",
        "twitch_connection": "Twitch 聊天連線",
        "channel": "頻道名稱",
        "connect": "連接 / 切換",
        "starting": "啟動中...",
        "insert_name": "插入名稱",
        "append_name": "加到最後",
        "viewer_name": "觀眾名稱",
        "move_up": "上移",
        "move_down": "下移",
        "delete": "刪除",
        "clear_queue": "清空隊列",
        "people_each": "每次叫號人數",
        "call_next": "叫下一位",
        "show_last_call": "重播上次叫號",
        "close_message": "關閉訊息",
        "show_queue": "顯示隊列",
        "hide_queue": "隱藏隊列",
        "accept_queue_on": "接受排隊：開",
        "accept_queue_off": "接受排隊：關",
        "obs_source": "OBS Browser Source",
        "call_source": "叫號 URL",
        "queue_source": "隊列 URL",
        "calendar_source": "月曆 URL",
        "calendar_tab": "月曆",
        "calendar_settings": "月曆設定",
        "queue_display_settings": "隊列顯示設定",
        "call_css": "叫號 CSS",
        "queue_css": "隊列 CSS",
        "calendar_css": "月曆 CSS",
        "weekday_text": "星期文字",
        "default_sound": "預設",
        "default_sound_installed": "預設音效已安裝：{name}",
        "calendar_first_text_label": "頭香時文本",
        "calendar_checkin_text_label": "簽到時文本",
        "calendar_command_text_label": "顯示月曆指令文本",
        "calendar_name_variable_hint": "名稱變數：{name}",
        "duration_zero_hint": "0 則常駐顯示",
        "calendar_display_seconds": "月曆顯示秒數",
        "calendar_time_zone": "時區",
        "custom_time_zone_offset": "UTC 偏移",
        "custom_time_zone_hint": "例：+1、-6、+5:30",
        "invalid_time_zone": "時區無效",
        "invalid_time_zone_message": "請輸入 UTC 偏移，例如 +8、UTC+9、+5:30 或 -6。",
        "calendar_csv_prefix": "月曆 CSV 前綴",
        "calendar_command_title": "顯示月曆指令",
        "calendar_command_hint": "觀眾訊息符合這些指令時會顯示月曆，可用 !月曆 2026-07。",
        "current_calendar_commands": "目前月曆指令",
        "calendar_displayed": "已顯示月曆",
        "manual_calendar_display": "手動顯示月曆",
        "manual_calendar_target": "目標人物名",
        "manual_calendar_month": "年月",
        "manual_calendar_month_hint": "空白 = 目前月份，格式：2026-06",
        "manual_calendar_show": "顯示月曆",
        "manual_calendar_missing_target": "請輸入目標人物名。",
        "manual_calendar_invalid_month": "年月格式必須是 YYYY-MM，例如 2026-06。",
        "manual_calendar_shown": "已為 {name} 顯示月曆",
        "calendar_checked_in": "{name} 已簽到",
        "streaming_tool_notice_title": "直播工具已開啟",
        "streaming_tool_notice_message": "偵測到 {tools} 可能已經開啟。\n\n如果 OBS / Streamlabs 的月曆、隊列或叫號畫面沒有顯示，請重新整理 Browser Source。",
        "css_version_notice_title": "CSS 版本檢查",
        "css_version_notice_message": "偵測到目前使用中的 CSS 可能是舊版或沒有版本標記：\n\n{files}\n\n選擇「是」：先備份舊 CSS，再盡量不改動原 CSS 的前提下進行必要更新。好處是保留自訂外觀，同時補上新版需要的相容內容；風險是如果 CSS 結構太舊，仍可能需要手動調整。\n\n選擇「否」：保持原狀。好處是自訂外觀完全不會被改動；風險是如果 CSS 結構太舊，OBS 顯示可能異常。",
        "css_updated_title": "CSS 已更新",
        "css_updated_message": "已更新 CSS，並建立備份：\n\n{files}",
        "css_update_failed_title": "CSS 更新失敗",
        "css_update_failed_message": "無法更新 CSS：{error}",
        "css_no_version": "沒有版本標記",
        "display_text": "叫號文字",
        "name_hint": "使用 {name} 代表觀眾名稱",
        "copy_url": "複製網址",
        "preview": "預覽",
        "general_settings": "一般設定",
        "port": "Port",
        "language": "介面語言",
        "display_seconds": "訊息顯示秒數",
        "queue_display_limit": "隊列顯示人數",
        "queue_display_seconds": "隊列顯示秒數",
        "sound_effect": "音效",
        "theme_css": "主題 CSS",
        "no_sound": "未指定",
        "default_theme": "default.css",
        "browse": "瀏覽...",
        "sound_selected": "音效已複製：{name}",
        "sound_copy_error": "無法複製音效",
        "theme_selected": "主題 CSS 已複製：{name}",
        "theme_copy_error": "無法複製主題 CSS",
        "apply": "套用設定",
        "join_command_title": "排隊指令",
        "queue_command_title": "顯示隊列指令",
        "add_command_title": "新增聊天指令",
        "add": "新增",
        "join_command_hint": "觀眾訊息完整符合任一指令時會加入隊列。",
        "queue_command_hint": "觀眾訊息完整符合任一指令時會在 OBS 顯示隊列。",
        "command_hint": "聊天訊息完整符合指令時觸發。",
        "current_commands": "目前指令",
        "current_join_commands": "目前排隊指令",
        "current_queue_commands": "目前顯示隊列指令",
        "delete_commands": "刪除選取指令",
        "blacklist_name": "黑名單名稱",
        "blacklist_hint": "名單內的 Twitch login 或顯示名稱不會觸發簽到，也會忽略所有指令。",
        "current_blacklist": "目前黑名單",
        "delete_blacklist": "刪除選取名稱",
        "blacklist_exists_title": "名稱已存在",
        "blacklist_exists": "{name} 已經在黑名單中。",
        "command_exists_title": "指令已存在",
        "command_exists": "{command} 已經在設定中。",
        "confirm_delete": "確認刪除",
        "confirm_delete_commands": "確定刪除選取的 {count} 個指令？",
        "confirm_delete_blacklist": "確定刪除選取的 {count} 個黑名單名稱？",
        "confirm_delete_viewers": "確定刪除選取的 {count} 位觀眾？",
        "empty_title": "隊列是空的",
        "empty_message": "目前沒有觀眾在隊列中。",
        "confirm_clear": "確認清空隊列",
        "confirm_clear_message": "確定清空目前 {count} 位觀眾？",
        "queue_cleared": "隊列已清空",
        "queue_displayed": "已顯示隊列",
        "queue_hidden": "已隱藏隊列",
        "message_closed": "訊息已關閉",
        "no_last_call": "沒有可重播的叫號",
        "called": "已叫號：{names}",
        "invalid_channel": "頻道名稱無效",
        "invalid_channel_message": "請輸入 Twitch 網址中的頻道名稱。",
        "connecting": "正在連接 #{channel}...",
        "url_copied": "OBS URL 已複製",
        "viewer_joined": "{name} 已透過聊天指令加入",
        "settings_applied": "設定已套用，OBS URL：{url}",
        "invalid_port": "Port 無效",
        "invalid_port_message": "Port 必須介於 1024 到 65535。",
        "invalid_seconds": "秒數無效",
        "invalid_seconds_message": "秒數必須介於 0 到 300。",
        "invalid_limit": "隊列顯示人數無效",
        "invalid_limit_message": "隊列顯示人數必須介於 1 到 100。",
        "port_error": "無法使用 Port",
        "port_error_message": "Port {port} 無法啟動：{error}",
        "connected": "已連接 #{channel}",
        "enter_channel": "請輸入 Twitch 頻道名稱",
        "disconnected": "連線中斷，5 秒後重試：{error}",
    },
    "en": {
        "app_title": "StreamerTool",
        "queue_tab": "Queue",
        "settings_tab": "Settings",
        "connection_log_tab": "Connection & Log",
        "command_settings_tab": "Command Settings",
        "blacklist_tab": "Blacklist",
        "queue_settings_tab": "Queue Settings",
        "log": "Log",
        "twitch_connection": "Twitch Chat Connection",
        "channel": "Channel",
        "connect": "Connect / Switch",
        "starting": "Starting...",
        "insert_name": "Insert Name",
        "append_name": "Add to End",
        "viewer_name": "Viewer Name",
        "move_up": "Move Up",
        "move_down": "Move Down",
        "delete": "Delete",
        "clear_queue": "Clear Queue",
        "people_each": "People per Call",
        "call_next": "Call Next",
        "show_last_call": "Replay Last Call",
        "close_message": "Close Message",
        "show_queue": "Show Queue",
        "hide_queue": "Hide Queue",
        "accept_queue_on": "Accept Queue: On",
        "accept_queue_off": "Accept Queue: Off",
        "obs_source": "OBS Browser Source",
        "call_source": "Call URL",
        "queue_source": "Queue URL",
        "calendar_source": "Calendar URL",
        "calendar_tab": "Calendar",
        "calendar_settings": "Calendar Settings",
        "queue_display_settings": "Queue Display Settings",
        "call_css": "Call CSS",
        "queue_css": "Queue CSS",
        "calendar_css": "Calendar CSS",
        "weekday_text": "Weekday Text",
        "default_sound": "Default",
        "default_sound_installed": "Default sound installed: {name}",
        "calendar_first_text_label": "First Check-in Text",
        "calendar_checkin_text_label": "Check-in Text",
        "calendar_command_text_label": "Show Calendar Command Text",
        "calendar_name_variable_hint": "Name variable: {name}",
        "duration_zero_hint": "0 keeps it visible",
        "calendar_display_seconds": "Calendar Display Duration (seconds)",
        "calendar_time_zone": "Time Zone",
        "custom_time_zone_offset": "UTC Offset",
        "custom_time_zone_hint": "Examples: +1, -6, +5:30",
        "invalid_time_zone": "Invalid Time Zone",
        "invalid_time_zone_message": "Use a UTC offset such as +8, UTC+9, +5:30, or -6.",
        "calendar_csv_prefix": "Calendar CSV Prefix",
        "calendar_command_title": "Show Calendar Commands",
        "calendar_command_hint": "Show the calendar when a viewer message matches one of these commands. Optional: !calendar 2026-07.",
        "current_calendar_commands": "Current Calendar Commands",
        "calendar_displayed": "Calendar shown in OBS",
        "manual_calendar_display": "Manual Calendar Display",
        "manual_calendar_target": "Target Name",
        "manual_calendar_month": "Year-Month",
        "manual_calendar_month_hint": "Blank = current month. Format: 2026-06",
        "manual_calendar_show": "Show Calendar",
        "manual_calendar_missing_target": "Enter a target name.",
        "manual_calendar_invalid_month": "Use YYYY-MM format, such as 2026-06.",
        "manual_calendar_shown": "Calendar shown for {name}",
        "calendar_checked_in": "{name} checked in",
        "streaming_tool_notice_title": "Streaming Tool Already Open",
        "streaming_tool_notice_message": "{tools} appears to be running.\n\nIf the calendar, queue, or call overlay does not appear in OBS / Streamlabs, refresh the Browser Source.",
        "css_version_notice_title": "CSS Version Check",
        "css_version_notice_message": "The currently selected CSS appears to be old or has no version marker:\n\n{files}\n\nChoose Yes: back up the old CSS, then apply the required update while changing the original CSS as little as possible. Benefit: custom styling is preserved while compatibility is updated. Risk: very old CSS may still need manual adjustment.\n\nChoose No: keep the CSS as-is. Benefit: custom appearance is fully preserved. Risk: older CSS may cause OBS display issues.",
        "css_updated_title": "CSS Updated",
        "css_updated_message": "CSS was updated and backups were created:\n\n{files}",
        "css_update_failed_title": "CSS Update Failed",
        "css_update_failed_message": "Could not update CSS: {error}",
        "css_no_version": "no version",
        "display_text": "Call Text",
        "name_hint": "Use {name} for viewer names",
        "copy_url": "Copy URL",
        "preview": "Preview",
        "general_settings": "General Settings",
        "port": "Port",
        "language": "Interface Language",
        "display_seconds": "Message Duration (seconds)",
        "queue_display_limit": "Queue Display Count",
        "queue_display_seconds": "Queue Display Duration (seconds)",
        "sound_effect": "Sound",
        "theme_css": "Theme CSS",
        "no_sound": "Not selected",
        "default_theme": "default.css",
        "browse": "Browse...",
        "sound_selected": "Sound copied: {name}",
        "sound_copy_error": "Could Not Copy Sound",
        "theme_selected": "Theme CSS copied: {name}",
        "theme_copy_error": "Could Not Copy Theme CSS",
        "apply": "Apply Settings",
        "join_command_title": "Join Queue Commands",
        "queue_command_title": "Show Queue Commands",
        "add_command_title": "Add Chat Command",
        "add": "Add",
        "join_command_hint": "A viewer joins the queue when their entire message matches any join command.",
        "queue_command_hint": "OBS shows the current queue when the entire message matches any show queue command.",
        "command_hint": "Triggers when the entire chat message matches a command.",
        "current_commands": "Current Commands",
        "current_join_commands": "Current Join Commands",
        "current_queue_commands": "Current Queue Commands",
        "delete_commands": "Delete Selected Commands",
        "blacklist_name": "Blacklist Name",
        "blacklist_hint": "Twitch login or display names on this list will not check in and all commands are ignored.",
        "current_blacklist": "Current Blacklist",
        "delete_blacklist": "Delete Selected Names",
        "blacklist_exists_title": "Name Exists",
        "blacklist_exists": "{name} is already on the blacklist.",
        "command_exists_title": "Command Exists",
        "command_exists": "{command} already exists.",
        "confirm_delete": "Confirm Delete",
        "confirm_delete_commands": "Delete {count} selected commands?",
        "confirm_delete_blacklist": "Delete {count} selected blacklist names?",
        "confirm_delete_viewers": "Delete {count} selected viewers?",
        "empty_title": "Queue Is Empty",
        "empty_message": "There are no viewers in the queue.",
        "confirm_clear": "Confirm Clear Queue",
        "confirm_clear_message": "Clear all {count} viewers from the queue?",
        "queue_cleared": "Queue cleared",
        "queue_displayed": "Queue shown",
        "queue_hidden": "Queue hidden",
        "message_closed": "Message closed",
        "no_last_call": "No previous call to replay",
        "called": "Called: {names}",
        "invalid_channel": "Invalid Channel",
        "invalid_channel_message": "Enter the channel name from the Twitch URL.",
        "connecting": "Connecting to #{channel}...",
        "url_copied": "OBS URL copied",
        "viewer_joined": "{name} joined via a chat command",
        "settings_applied": "Settings applied. OBS URL: {url}",
        "invalid_port": "Invalid Port",
        "invalid_port_message": "Port must be between 1024 and 65535.",
        "invalid_seconds": "Invalid Seconds",
        "invalid_seconds_message": "Seconds must be between 0 and 300.",
        "invalid_limit": "Invalid Queue Count",
        "invalid_limit_message": "Queue display count must be between 1 and 100.",
        "port_error": "Could Not Use Port",
        "port_error_message": "Port {port} could not start: {error}",
        "connected": "Connected to #{channel}",
        "enter_channel": "Enter a Twitch channel name",
        "disconnected": "Disconnected, retrying in 5 seconds: {error}",
    },
    "ja": {}
}
TRANSLATIONS["ja"] = TRANSLATIONS["en"].copy()
TRANSLATIONS["ja"].update({
    "queue_tab": "キュー",
    "settings_tab": "設定",
    "connection_log_tab": "接続とログ",
    "command_settings_tab": "コマンド設定",
    "blacklist_tab": "ブラックリスト",
    "queue_settings_tab": "キュー設定",
    "log": "ログ",
    "general_settings": "一般設定",
    "calendar_settings": "カレンダー設定",
    "calendar_time_zone": "タイムゾーン",
    "custom_time_zone_offset": "UTC オフセット",
    "custom_time_zone_hint": "例: +1、-6、+5:30",
    "invalid_time_zone": "タイムゾーンが無効です",
    "invalid_time_zone_message": "+8、UTC+9、+5:30、-6 のような UTC オフセットを入力してください。",
    "queue_display_settings": "キュー表示設定",
    "weekday_text": "曜日表示",
    "default_sound": "標準",
    "default_sound_installed": "標準効果音を設定しました: {name}",
    "calendar_first_text_label": "一番乗りテキスト",
    "calendar_checkin_text_label": "チェックイン時テキスト",
    "calendar_command_text_label": "カレンダー表示コマンド時テキスト",
    "calendar_name_variable_hint": "名前変数: {name}",
    "manual_calendar_display": "手動カレンダー表示",
    "manual_calendar_target": "対象名",
    "manual_calendar_month": "年月",
    "manual_calendar_month_hint": "空白 = 今月、形式: 2026-06",
    "manual_calendar_show": "カレンダー表示",
    "manual_calendar_missing_target": "対象名を入力してください。",
    "manual_calendar_invalid_month": "YYYY-MM 形式で入力してください。例: 2026-06",
    "manual_calendar_shown": "{name} のカレンダーを表示しました",
    "streaming_tool_notice_title": "配信ツールが起動中です",
    "streaming_tool_notice_message": "{tools} が起動している可能性があります。\n\nOBS / Streamlabs でカレンダー、キュー、呼び出し画面が表示されない場合は、Browser Source を更新してください。",
    "css_version_notice_title": "CSS バージョン確認",
    "css_version_notice_message": "現在使用中の CSS が古い、またはバージョン表記がありません:\n\n{files}\n\n「はい」: 古い CSS をバックアップして、元の CSS をできるだけ変更せずに必要な更新を行います。利点はカスタム表示を保ちながら互換性を更新できることです。リスクは非常に古い CSS では手動調整が必要になる可能性があることです。\n\n「いいえ」: そのまま使用します。利点はカスタム表示を完全に維持できることです。リスクは古い CSS により OBS 表示が崩れる可能性があることです。",
    "css_updated_title": "CSS を更新しました",
    "css_updated_message": "CSS を更新し、バックアップを作成しました:\n\n{files}",
    "css_update_failed_title": "CSS 更新失敗",
    "css_update_failed_message": "CSS を更新できませんでした: {error}",
    "css_no_version": "バージョン表記なし",
    "duration_zero_hint": "0 は常時表示",
    "blacklist_name": "ブラックリスト名",
    "blacklist_hint": "このリストの Twitch ログイン名または表示名はチェックインせず、すべてのコマンドも無視します。",
    "current_blacklist": "現在のブラックリスト",
    "delete_blacklist": "選択した名前を削除",
    "blacklist_exists_title": "名前は登録済みです",
    "blacklist_exists": "{name} はすでにブラックリストにあります。",
    "confirm_delete_blacklist": "選択した {count} 件のブラックリスト名を削除しますか？",
    "sound_effect": "効果音",
    "apply": "設定を適用",
    "browse": "参照...",
    "show_last_call": "前回の呼び出し",
    "close_message": "メッセージを閉じる",
    "show_queue": "キューを表示",
    "hide_queue": "キューを非表示",
    "queue_displayed": "キューを表示しました",
    "queue_hidden": "キューを非表示にしました",
    "message_closed": "メッセージを閉じました",
    "no_last_call": "再生できる前回の呼び出しがありません",
})


def translate(key: str, **values) -> str:
    state = globals().get("STATE")
    language = getattr(state, "language", "zh")
    text = TRANSLATIONS.get(language, TRANSLATIONS["zh"]).get(key, key)
    return text.format(**values) if values else text


def detect_default_language() -> str:
    language = ""
    try:
        language = (locale.getlocale()[0] or "").casefold()
    except (ValueError, TypeError):
        language = ""
    if not language:
        language = (os.environ.get("LANG") or "").casefold()
    if language.startswith("zh") or "chinese" in language or "銝剜?" in language:
        return "zh"
    if language.startswith("ja") or "japanese" in language:
        return "ja"
    if language.startswith("en") or "english" in language:
        return "en"
    return "en"


def default_calendar_texts(language: str) -> dict[str, str]:
    if language == "zh":
        return {
            "first": "\U0001f451 {name} 頭香！",
            "checkin": "{name} 簽到成功",
            "command": "{name} 顯示月曆",
        }
    if language == "ja":
        return {
            "first": "\U0001f451 {name} が本日の一番乗り！",
            "checkin": "{name} がチェックインしました",
            "command": "{name} がカレンダーを表示しました",
        }
    return {
        "first": "\U0001f451 {name} is first today!",
        "checkin": "{name} checked in",
        "command": "{name} shows the calendar",
    }

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


def normalize_blacklist_name(value: str) -> str:
    return str(value or "").strip().lstrip("@").casefold()


def detect_running_streaming_tools() -> list[str]:
    if os.name != "nt":
        return []
    try:
        result = subprocess.run(
            ["tasklist", "/fo", "csv", "/nh"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            timeout=3,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return []
    if result.returncode != 0:
        return []
    found: list[str] = []
    for row in csv.reader(result.stdout.splitlines()):
        if not row:
            continue
        process_name = row[0].strip().casefold()
        tool_name = STREAMING_TOOL_PROCESSES.get(process_name)
        if tool_name and tool_name not in found:
            found.append(tool_name)
    return found


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


class State:
    def __init__(self) -> None:
        SETTING_DIR.mkdir(parents=True, exist_ok=True)
        CSS_DIR.mkdir(parents=True, exist_ok=True)
        CALL_CSS_DIR.mkdir(parents=True, exist_ok=True)
        QUEUE_CSS_DIR.mkdir(parents=True, exist_ok=True)
        CALENDAR_CSS_DIR.mkdir(parents=True, exist_ok=True)
        AUDIO_DIR.mkdir(parents=True, exist_ok=True)
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
        self.calendar_time_zone = detect_default_time_zone_label()
        self.calendar_weekday_language = normalize_weekday_language(self.language, "zh")
        self.calendar_csv_prefix = ""
        calendar_texts = default_calendar_texts(self.language)
        self.calendar_first_text = calendar_texts["first"]
        self.calendar_checkin_text = calendar_texts["checkin"]
        self.calendar_command_text = calendar_texts["command"]
        self.sound_file = DEFAULT_AUDIO_FILE if (AUDIO_DIR / DEFAULT_AUDIO_FILE).is_file() else ""
        self.calendar_sound_file = DEFAULT_AUDIO_FILE if (AUDIO_DIR / DEFAULT_AUDIO_FILE).is_file() else ""
        self.css_file = "default.css"
        self.call_css_file = "default.css"
        self.queue_css_file = "default.css"
        self.calendar_css_file = "default.css"
        self.commands = list(DEFAULT_JOIN_COMMANDS)
        self.queue_commands = list(DEFAULT_QUEUE_COMMANDS)
        self.calendar_commands = list(DEFAULT_CALENDAR_COMMANDS)
        self.blacklist_names = list(DEFAULT_BLACKLIST_NAMES)
        self.last_called_names: list[str] = []
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
            css_file = Path(str(data.get("css_file", "default.css"))).name
            self.css_file = css_file if css_file else "default.css"
            self.call_css_file = Path(str(data.get("call_css_file", self.css_file))).name or "default.css"
            self.queue_css_file = Path(str(data.get("queue_css_file", self.css_file))).name or "default.css"
            self.calendar_css_file = Path(str(data.get("calendar_css_file", self.css_file))).name or "default.css"
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
                "calendar_time_zone": self.calendar_time_zone,
                "calendar_weekday_language": self.calendar_weekday_language,
                "calendar_csv_prefix": self.calendar_csv_prefix,
                "calendar_first_text": self.calendar_first_text,
                "calendar_checkin_text": self.calendar_checkin_text,
                "calendar_command_text": self.calendar_command_text,
                "sound_file": self.sound_file,
                "calendar_sound_file": self.calendar_sound_file,
                "css_file": self.css_file,
                "call_css_file": self.call_css_file,
                "queue_css_file": self.queue_css_file,
                "calendar_css_file": self.calendar_css_file,
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
        sound_path = active_audio_path(self.sound_file)
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
            for overlay in (self.overlay_event["call"], self.overlay_event["queue"], self.overlay_event["calendar"]):
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

    def show_calendar(
        self,
        username: str,
        display_name: str,
        date_override: tuple[int, int] | None = None,
        command_only: bool = False,
    ) -> bool:
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
            calendar_sound_path = active_audio_path(self.calendar_sound_file) if signed_date else None
            calendar_overlay = self.overlay_event["calendar"]
            calendar_overlay.update(
                {
                    "id": calendar_overlay["id"] + 1,
                    "year": year,
                    "month": month,
                    "today": today,
                    "username": username,
                    "display_name": display_name,
                    "message": message,
                    "dates": user_dates,
                    "signed_date": signed_date,
                    "duration_ms": self.calendar_display_seconds * 1000,
                    "sound_url": "/audio/calendar" if calendar_sound_path else "",
                    "weekday_language": self.calendar_weekday_language,
                    "visible": True,
                    "created_at": time.time(),
                }
            )
            return True


STATE = State()
UI_EVENTS: queue.Queue[tuple[str, str]] = queue.Queue()


def ensure_default_css() -> None:
    for directory in (CSS_DIR, CALL_CSS_DIR, QUEUE_CSS_DIR, CALENDAR_CSS_DIR):
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


def selected_css_entries() -> list[tuple[str, Path]]:
    ensure_default_css()
    entries: list[tuple[str, Path]] = []
    area_map = {
        "call": (CALL_CSS_DIR, "call_css_file"),
        "queue": (QUEUE_CSS_DIR, "queue_css_file"),
        "calendar": (CALENDAR_CSS_DIR, "calendar_css_file"),
    }
    with STATE.lock:
        for area, (css_dir, state_attr) in area_map.items():
            css_file = Path(getattr(STATE, state_attr, "default.css") or "default.css").name
            css_path = css_dir / css_file
            if css_path.is_file():
                entries.append((area, css_path))
    return entries


def outdated_selected_css_entries() -> list[tuple[str, Path, int | None]]:
    outdated: list[tuple[str, Path, int | None]] = []
    seen: set[Path] = set()
    for area, css_path in selected_css_entries():
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


def active_css_path(area: str) -> Path:
    ensure_default_css()
    area_map = {
        "call": (CALL_CSS_DIR, "call_css_file", CALL_CSS_FILE),
        "queue": (QUEUE_CSS_DIR, "queue_css_file", QUEUE_CSS_FILE),
        "calendar": (CALENDAR_CSS_DIR, "calendar_css_file", CALENDAR_CSS_FILE),
    }
    css_dir, state_attr, default_path = area_map.get(area, area_map["call"])
    with STATE.lock:
        css_file = Path(getattr(STATE, state_attr, "default.css") or "default.css").name
        css_path = css_dir / css_file
        if not css_path.is_file():
            setattr(STATE, state_attr, "default.css")
            STATE.save()
            css_path = default_path
    return css_path


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


CALL_OVERLAY_HTML = """<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8">
<link rel="stylesheet" href="/css/call/default.css"></head><body>
<div id="overlay-container">
  <section id="call-area" class="overlay-area">
    <div id="call-message" class="overlay-message" hidden></div>
  </section>
</div>
<script>
let lastCallId=0, callTimer;
const sound=new Audio();
sound.preload='auto';
function showBox(box){
  box.hidden=false;
  box.classList.add('show');
}
function hideBox(box){
  box.classList.remove('show');
  box.hidden=true;
}
function renderCharacters(box,text){
  box.replaceChildren();
  Array.from(text).forEach((character,index)=>{
    const span=document.createElement('span');
    span.className='char';
    span.style.setProperty('--char-index',index);
    span.textContent=character;
    box.appendChild(span);
  });
}
async function update(){
  try{
    const data=await fetch('/api/overlay',{cache:'no-store'}).then(r=>r.json());
    const call=data.call || {};
    if(call.id>lastCallId){
      lastCallId=call.id;
      const box=document.getElementById('call-message');
      clearTimeout(callTimer);
      if(call.visible && call.text){
        renderCharacters(box,call.text);
        showBox(box);
      }else{
        hideBox(box);
      }
      if(call.sound_url){
        sound.pause();
        sound.src=call.sound_url+'?event='+call.id;
        sound.currentTime=0;
        sound.play().catch(()=>{});
      }
      if(call.visible && call.duration_ms>0){
        callTimer=setTimeout(()=>hideBox(box),call.duration_ms);
      }
    }
  }catch(e){}
}
setInterval(update,400); update();
</script></body></html>"""


QUEUE_OVERLAY_HTML = """<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8">
<link rel="stylesheet" href="/css/queue/default.css"></head><body>
<div id="overlay-container">
  <section id="queue-area" class="overlay-area">
    <div id="queue-message" class="overlay-message" hidden></div>
  </section>
</div>
<script>
let lastQueueId=0, queueTimer;
function showBox(box){
  box.hidden=false;
  box.classList.add('show');
}
function hideBox(box){
  box.classList.remove('show');
  box.hidden=true;
}
function renderQueue(box,items,hasMore){
  box.replaceChildren();
  const list=document.createElement('ol');
  list.className='queue-list';
  items.forEach(name=>{
    const item=document.createElement('li');
    item.textContent=name;
    list.appendChild(item);
  });
  if(hasMore){
    const item=document.createElement('li');
    item.className='queue-more';
    item.textContent='...';
    list.appendChild(item);
  }
  box.appendChild(list);
}
async function update(){
  try{
    const data=await fetch('/api/overlay',{cache:'no-store'}).then(r=>r.json());
    const queue=data.queue || {};
    if(queue.id>lastQueueId){
      lastQueueId=queue.id;
      const box=document.getElementById('queue-message');
      clearTimeout(queueTimer);
      if(queue.visible){
        renderQueue(box,queue.items || [], !!queue.has_more);
        showBox(box);
      }else{
        hideBox(box);
      }
      if(queue.visible && queue.duration_ms>0){
        queueTimer=setTimeout(()=>hideBox(box),queue.duration_ms);
      }
    }
  }catch(e){}
}
setInterval(update,400); update();
</script></body></html>"""


CALENDAR_OVERLAY_HTML = """<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8">
<link rel="stylesheet" href="/css/calendar/default.css"></head><body>
<div class="calendar-container" id="calendarBox">
  <div class="banner-alert" id="alertText">Twitch Check-in Calendar</div>
  <div class="calendar-header" id="calendarTitle"></div>
  <div class="days-grid" id="daysGrid"></div>
</div>
<script>
let lastCalendarId=0, calendarTimer;
const dayCells={};
const calendarSound=new Audio();
calendarSound.preload='auto';
const weekdayLabels={
  zh:['\u65e5','\u4e00','\u4e8c','\u4e09','\u56db','\u4e94','\u516d'],
  en:['Sun','Mon','Tue','Wed','Thu','Fri','Sat'],
  ja:['\u65e5','\u6708','\u706b','\u6c34','\u6728','\u91d1','\u571f']
};
const box=document.getElementById('calendarBox');
const grid=document.getElementById('daysGrid');
const alertText=document.getElementById('alertText');
function fallbackAvatar(name){
  const initial=Array.from(String(name || '?').trim())[0] || '?';
  const svg=`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120"><rect width="120" height="120" rx="18" fill="#9146ff"/><text x="60" y="75" text-anchor="middle" font-family="Arial,sans-serif" font-size="54" font-weight="700" fill="#fff">${initial.replace(/[&<>]/g,'')}</text></svg>`;
  return 'data:image/svg+xml;charset=utf-8,'+encodeURIComponent(svg);
}
function showBox(){
  box.classList.add('show');
}
function hideBox(){
  box.classList.remove('show');
}
function rebuildCalendar(year,month,today,weekdayLanguage){
  grid.replaceChildren();
  Object.keys(dayCells).forEach(key=>delete dayCells[key]);
  const weekdays=weekdayLabels[weekdayLanguage] || weekdayLabels.zh;
  weekdays.forEach(label=>{
    const weekday=document.createElement('div');
    weekday.className='day-name';
    weekday.textContent=label;
    grid.appendChild(weekday);
  });
  document.getElementById('calendarTitle').textContent=`${year} / ${String(month).padStart(2,'0')}`;
  const first=new Date(year,month-1,1).getDay();
  const total=new Date(year,month,0).getDate();
  for(let i=0;i<first;i++){
    const empty=document.createElement('div');
    empty.className='empty-day';
    grid.appendChild(empty);
  }
  for(let day=1;day<=total;day++){
    const cell=document.createElement('div');
    cell.className='day';
    const number=document.createElement('div');
    number.className='day-number';
    number.textContent=day;
    cell.appendChild(number);
    if(day===today){
      cell.classList.add('today-day');
    }
    grid.appendChild(cell);
    dayCells[day]=cell;
  }
}
function clearAllAvatars(){
  Object.values(dayCells).forEach(cell=>{
    cell.classList.remove('first-stamp-day');
    cell.querySelectorAll('img.user-avatar').forEach(img=>img.remove());
  });
}
function renderUserDates(calendar){
  clearAllAvatars();
  const animateDate=calendar.signed_date || '';
  const username=String(calendar.username || '').trim();
  const avatarUrl=username ? `https://unavatar.io/twitch/${encodeURIComponent(username)}` : '';
  (calendar.dates || []).forEach(item=>{
    const parts=String(item.date || '').split('-');
    const day=Number(parts[2]);
    const cell=dayCells[day];
    if(!cell) return;
    if(item.isFirst){
      cell.classList.add('first-stamp-day');
    }
    if(avatarUrl){
      const img=document.createElement('img');
      img.className='user-avatar';
      img.src=avatarUrl;
      img.alt='';
      img.onerror=()=>{ img.onerror=null; img.src=fallbackAvatar(calendar.display_name); };
      cell.appendChild(img);
      if(animateDate && item.date===animateDate){
        requestAnimationFrame(()=>img.classList.add('stamp-animation'));
      }
    }
  });
}
function renderCalendar(calendar){
  rebuildCalendar(calendar.year,calendar.month,calendar.today || 0, calendar.weekday_language || 'zh');
  alertText.textContent=calendar.message || 'Twitch Check-in Calendar';
  renderUserDates(calendar);
}
async function update(){
  try{
    const data=await fetch('/api/overlay',{cache:'no-store'}).then(r=>r.json());
    const calendar=data.calendar || {};
    if(calendar.id>lastCalendarId){
      lastCalendarId=calendar.id;
      clearTimeout(calendarTimer);
      if(calendar.visible){
        renderCalendar(calendar);
        showBox();
        if(calendar.sound_url){
          calendarSound.pause();
          calendarSound.currentTime=0;
          calendarSound.src=calendar.sound_url+'?event='+calendar.id;
          calendarSound.play().catch(()=>{});
        }
      }else{
        hideBox();
      }
      if(calendar.visible && calendar.duration_ms>0){
        calendarTimer=setTimeout(hideBox,calendar.duration_ms);
      }
    }
  }catch(e){}
}
setInterval(update,400); update();
</script></body></html>"""


class OverlayHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path in ("/", "/call"):
            body = CALL_OVERLAY_HTML.encode("utf-8")
            content_type = "text/html; charset=utf-8"
        elif path == "/queue":
            body = QUEUE_OVERLAY_HTML.encode("utf-8")
            content_type = "text/html; charset=utf-8"
        elif path == "/calendar":
            body = CALENDAR_OVERLAY_HTML.encode("utf-8")
            content_type = "text/html; charset=utf-8"
        elif path == "/overlay":
            body = CALL_OVERLAY_HTML.encode("utf-8")
            content_type = "text/html; charset=utf-8"
        elif path == "/api/overlay":
            STATE.expire_overlays()
            with STATE.lock:
                body = json.dumps(STATE.overlay_event, ensure_ascii=False).encode("utf-8")
            content_type = "application/json; charset=utf-8"
        elif path in ("/default.css", "/css/call/default.css"):
            try:
                body = active_css_path("call").read_bytes()
            except FileNotFoundError:
                self.send_error(404)
                return
            content_type = "text/css; charset=utf-8"
        elif path == "/css/queue/default.css":
            try:
                body = active_css_path("queue").read_bytes()
            except FileNotFoundError:
                self.send_error(404)
                return
            content_type = "text/css; charset=utf-8"
        elif path == "/css/calendar/default.css":
            try:
                body = active_css_path("calendar").read_bytes()
            except FileNotFoundError:
                self.send_error(404)
                return
            content_type = "text/css; charset=utf-8"
        elif path in ("/sound", "/audio/call", "/audio/calendar"):
            with STATE.lock:
                sound_file = STATE.calendar_sound_file if path == "/audio/calendar" else STATE.sound_file
            sound_path = active_audio_path(sound_file)
            if not sound_path or not sound_path.is_file():
                self.send_error(404)
                return
            body = sound_path.read_bytes()
            content_type = mimetypes.guess_type(sound_path.name)[0] or "application/octet-stream"
        else:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args) -> None:
        pass


class ServerManager:
    def __init__(self, port: int) -> None:
        self.server: ThreadingHTTPServer | None = None
        self.thread: threading.Thread | None = None
        self.port = port

    def start(self) -> None:
        self.server = ThreadingHTTPServer((HOST, self.port), OverlayHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def restart(self, port: int) -> None:
        if port == self.port:
            return
        new_server = ThreadingHTTPServer((HOST, port), OverlayHandler)
        new_thread = threading.Thread(target=new_server.serve_forever, daemon=True)
        new_thread.start()
        old_server = self.server
        self.server = new_server
        self.thread = new_thread
        self.port = port
        if old_server:
            old_server.shutdown()
            old_server.server_close()

    def stop(self) -> None:
        if self.server:
            self.server.shutdown()
            self.server.server_close()


class TwitchChat(threading.Thread):
    def __init__(self) -> None:
        super().__init__(daemon=True)
        self.stop_event = threading.Event()
        self.reconnect_event = threading.Event()

    def reconnect(self) -> None:
        self.reconnect_event.set()

    def stop(self) -> None:
        self.stop_event.set()
        self.reconnect_event.set()

    @staticmethod
    def _send_frame(sock: ssl.SSLSocket, text: str) -> None:
        payload = text.encode("utf-8")
        mask = secrets.token_bytes(4)
        length = len(payload)
        header = bytearray([0x81])
        if length < 126:
            header.append(0x80 | length)
        elif length < 65536:
            header.extend([0x80 | 126])
            header.extend(struct.pack("!H", length))
        else:
            header.extend([0x80 | 127])
            header.extend(struct.pack("!Q", length))
        masked = bytes(byte ^ mask[i % 4] for i, byte in enumerate(payload))
        sock.sendall(bytes(header) + mask + masked)

    @staticmethod
    def _recv_exact(sock: ssl.SSLSocket, size: int) -> bytes:
        data = b""
        while len(data) < size:
            chunk = sock.recv(size - len(data))
            if not chunk:
                raise ConnectionError("connection closed")
            data += chunk
        return data

    def _recv_frame(self, sock: ssl.SSLSocket) -> tuple[int, bytes]:
        first, second = self._recv_exact(sock, 2)
        opcode = first & 0x0F
        length = second & 0x7F
        if length == 126:
            length = struct.unpack("!H", self._recv_exact(sock, 2))[0]
        elif length == 127:
            length = struct.unpack("!Q", self._recv_exact(sock, 8))[0]
        mask = self._recv_exact(sock, 4) if second & 0x80 else None
        payload = self._recv_exact(sock, length)
        if mask:
            payload = bytes(byte ^ mask[i % 4] for i, byte in enumerate(payload))
        return opcode, payload

    def _connect(self, channel: str) -> None:
        raw = socket.create_connection(("irc-ws.chat.twitch.tv", 443), timeout=12)
        sock = ssl.create_default_context().wrap_socket(raw, server_hostname="irc-ws.chat.twitch.tv")
        key = base64.b64encode(secrets.token_bytes(16)).decode()
        request = (
            "GET / HTTP/1.1\r\nHost: irc-ws.chat.twitch.tv\r\nUpgrade: websocket\r\n"
            "Connection: Upgrade\r\nOrigin: https://www.twitch.tv\r\n"
            f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n"
        )
        sock.sendall(request.encode())
        response = b""
        while b"\r\n\r\n" not in response:
            response += sock.recv(1024)
        expected = base64.b64encode(
            hashlib.sha1((key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode()).digest()
        ).decode()
        if b"101" not in response.split(b"\r\n", 1)[0] or expected.encode() not in response:
            raise ConnectionError("WebSocket ?⊥?憭望?")

        nick = f"justinfan{secrets.randbelow(80000) + 1000}"
        self._send_frame(sock, "PASS SCHMOOPIE")
        self._send_frame(sock, f"NICK {nick}")
        self._send_frame(sock, "CAP REQ :twitch.tv/tags twitch.tv/commands")
        self._send_frame(sock, f"JOIN #{channel}")
        sock.settimeout(2)
        UI_EVENTS.put(("status", translate("connected", channel=channel)))
        buffer = ""
        last_frame_at = time.time()
        try:
            while not self.stop_event.is_set() and not self.reconnect_event.is_set():
                try:
                    opcode, payload = self._recv_frame(sock)
                except socket.timeout:
                    if time.time() - last_frame_at > CHAT_IDLE_TIMEOUT_SECONDS:
                        raise TimeoutError("Twitch chat idle timeout")
                    continue
                last_frame_at = time.time()
                if opcode == 8:
                    break
                if opcode == 9:
                    # Server ping frame; client pong frame, unmasked server payload.
                    self._send_pong(sock, payload)
                    continue
                if opcode != 1:
                    continue
                buffer += payload.decode("utf-8", errors="replace")
                lines = buffer.split("\r\n")
                buffer = lines.pop()
                for line in lines:
                    if line.startswith("PING"):
                        self._send_frame(sock, line.replace("PING", "PONG", 1) + "\r\n")
                    else:
                        self._handle_line(line)
        finally:
            sock.close()

    @staticmethod
    def _send_pong(sock: ssl.SSLSocket, payload: bytes) -> None:
        mask = secrets.token_bytes(4)
        masked = bytes(byte ^ mask[i % 4] for i, byte in enumerate(payload))
        sock.sendall(bytes([0x8A, 0x80 | len(payload)]) + mask + masked)

    @staticmethod
    def _parse_calendar_command(text: str, commands: list[str]) -> tuple[bool, tuple[int, int] | None]:
        message = text.strip()
        folded = message.casefold()
        for command in sorted(commands, key=len, reverse=True):
            command_text = command.strip()
            if not command_text:
                continue
            if not folded.startswith(command_text.casefold()):
                continue
            rest = message[len(command_text):].strip()
            if not rest:
                return True, None
            parts = rest.replace("/", "-").split("-")
            if len(parts) == 2:
                try:
                    year = int(parts[0])
                    month = int(parts[1])
                except ValueError:
                    return True, None
                if 2000 <= year <= 2099 and 1 <= month <= 12:
                    return True, (year, month)
            return True, None
        return False, None

    @staticmethod
    def _parse_twitch_sender(prefix: str) -> tuple[dict[str, str], str, str]:
        tags: dict[str, str] = {}
        source = prefix.strip()
        if source.startswith("@"):
            tag_text, _, source = source.partition(" ")
            tags = dict(item.partition("=")[::2] for item in tag_text[1:].split(";"))
        source = source.strip()
        if source.startswith(":"):
            source = source[1:]
        login = source.split("!", 1)[0].strip().lower()
        display_name = tags.get("display-name", "").strip()
        return tags, login, display_name

    @staticmethod
    def _handle_line(line: str) -> None:
        if " PRIVMSG #" not in line:
            return
        prefix, _, message = line.partition(" PRIVMSG #")
        _, _, text = message.partition(" :")
        _tags, login, display_name = TwitchChat._parse_twitch_sender(prefix)
        if not login:
            return
        with STATE.lock:
            is_blacklisted = STATE.is_blacklisted(login, display_name)
        if is_blacklisted:
            return
        command = text.strip().casefold()
        with STATE.lock:
            join_matches = {item.casefold() for item in STATE.commands}
            queue_matches = {item.casefold() for item in STATE.queue_commands}
            calendar_commands = list(STATE.calendar_commands)
        is_join_command = command in join_matches
        is_queue_command = command in queue_matches
        is_calendar_command, calendar_override = TwitchChat._parse_calendar_command(text, calendar_commands)
        if is_queue_command:
            STATE.show_queue_overlay()
            UI_EVENTS.put(("queue_display", ""))
        if display_name and login and display_name.casefold() != login.casefold():
            name = f"{display_name}({login})"
        else:
            name = display_name or login
        is_any_command = is_join_command or is_queue_command or is_calendar_command
        if login and name and (is_calendar_command or not is_any_command):
            if STATE.show_calendar(login, display_name or login, calendar_override, is_any_command):
                UI_EVENTS.put(("calendar", name))
        if is_join_command and name and STATE.add_viewer(name):
            UI_EVENTS.put(("queue", name))

    def run(self) -> None:
        while not self.stop_event.is_set():
            self.reconnect_event.clear()
            with STATE.lock:
                channel = STATE.channel
            if not channel:
                UI_EVENTS.put(("status", translate("enter_channel")))
                self.reconnect_event.wait(1)
                continue
            try:
                self._connect(channel)
            except Exception as exc:
                if not self.stop_event.is_set() and not self.reconnect_event.is_set():
                    UI_EVENTS.put(("status", translate("disconnected", error=exc)))
                    self.reconnect_event.wait(5)


class App:
    def __init__(self, root: tk.Tk, chat: TwitchChat, server_manager: ServerManager) -> None:
        self.root = root
        self.chat = chat
        self.server_manager = server_manager
        root.title(f"{self.tr('app_title')} v{APP_VERSION}")
        root.geometry("900x700")
        root.minsize(760, 540)
        root.protocol("WM_DELETE_WINDOW", self.close)
        self._build()
        self.refresh()
        self.poll_events()
        self.root.after(800, self.show_streaming_tool_notice_if_needed)
        self.root.after(1200, self.show_css_version_notice_if_needed)

    @staticmethod
    def tr(key: str, **values) -> str:
        return translate(key, **values)

    def set_action_status(self, message: str) -> None:
        if hasattr(self, "action_status_var"):
            self.action_status_var.set(message)
        if message and hasattr(self, "log_list"):
            stamp = time.strftime("%H:%M:%S")
            self.log_list.insert(tk.END, f"[{stamp}] {message}")
            overflow = self.log_list.size() - LOG_MAX_LINES
            if overflow > 0:
                self.log_list.delete(0, overflow - 1)
            self.log_list.see(tk.END)

    def show_streaming_tool_notice_if_needed(self) -> None:
        if not HAS_EXISTING_STATE_FILE:
            return
        tools = detect_running_streaming_tools()
        if not tools:
            return
        messagebox.showinfo(
            self.tr("streaming_tool_notice_title"),
            self.tr("streaming_tool_notice_message", tools=", ".join(tools)),
            parent=self.root,
        )

    def css_area_label(self, area: str) -> str:
        labels = {
            "call": self.tr("call_css"),
            "queue": self.tr("queue_css"),
            "calendar": self.tr("calendar_css"),
        }
        return labels.get(area, area)

    def show_css_version_notice_if_needed(self) -> None:
        outdated_entries = outdated_selected_css_entries()
        if not outdated_entries:
            return
        file_lines = []
        for area, css_path, version in outdated_entries:
            version_text = f"v{version}" if version is not None else self.tr("css_no_version")
            file_lines.append(f"- {self.css_area_label(area)}: {css_path.name} ({version_text})")
        should_update = messagebox.askyesno(
            self.tr("css_version_notice_title"),
            self.tr("css_version_notice_message", files="\n".join(file_lines), version=CSS_VERSION),
            parent=self.root,
        )
        if not should_update:
            return
        try:
            backup_lines = []
            for area, css_path, version in outdated_entries:
                backup_path = backup_and_migrate_css(area, css_path, version)
                backup_lines.append(f"- {self.css_area_label(area)}: backup/{backup_path.name}")
        except OSError as exc:
            messagebox.showerror(
                self.tr("css_update_failed_title"),
                self.tr("css_update_failed_message", error=exc),
                parent=self.root,
            )
            return
        messagebox.showinfo(
            self.tr("css_updated_title"),
            self.tr("css_updated_message", files="\n".join(backup_lines)),
            parent=self.root,
        )

    def _build(self) -> None:
        self.root.title(f"{self.tr('app_title')} v{APP_VERSION}")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        style = ttk.Style()
        style.configure("Treeview", rowheight=30, font=("", 11))
        style.configure("Treeview.Heading", font=("", 11, "bold"))
        style.configure("CallNext.TButton", font=("", 13, "bold"), padding=(18, 10))

        notebook = ttk.Notebook(self.root)
        notebook.grid(row=0, column=0, sticky="nsew")

        self.connection_tab = ttk.Frame(notebook)
        self.queue_tab = ttk.Frame(notebook)
        self.general_tab = ttk.Frame(notebook)
        self.command_tab = ttk.Frame(notebook)
        self.blacklist_tab = ttk.Frame(notebook)
        self.queue_settings_tab = ttk.Frame(notebook)
        self.calendar_settings_tab = ttk.Frame(notebook)
        notebook.add(self.connection_tab, text=self.tr("connection_log_tab"))
        notebook.add(self.queue_tab, text=self.tr("queue_tab"))
        notebook.add(self.general_tab, text=self.tr("general_settings"))
        notebook.add(self.command_tab, text=self.tr("command_settings_tab"))
        notebook.add(self.blacklist_tab, text=self.tr("blacklist_tab"))
        notebook.add(self.queue_settings_tab, text=self.tr("queue_settings_tab"))
        notebook.add(self.calendar_settings_tab, text=self.tr("calendar_settings"))

        self.connection_tab.columnconfigure(0, weight=1)
        self.connection_tab.rowconfigure(1, weight=1)
        channel_frame = ttk.LabelFrame(self.connection_tab, text=self.tr("twitch_connection"), padding=10)
        channel_frame.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 6))
        channel_frame.columnconfigure(1, weight=1)
        ttk.Label(channel_frame, text=self.tr("channel")).grid(row=0, column=0, padx=(0, 8))
        self.channel_var = tk.StringVar(value=STATE.channel)
        ttk.Entry(channel_frame, textvariable=self.channel_var).grid(row=0, column=1, sticky="ew")
        ttk.Button(channel_frame, text=self.tr("connect"), command=self.change_channel).grid(row=0, column=2, padx=(8, 0))
        self.status_var = tk.StringVar(value=self.tr("starting"))
        ttk.Label(channel_frame, textvariable=self.status_var).grid(row=1, column=0, columnspan=3, sticky="w", pady=(7, 0))
        self.action_status_var = tk.StringVar(value="")
        ttk.Label(channel_frame, textvariable=self.action_status_var).grid(row=2, column=0, columnspan=3, sticky="w", pady=(4, 0))

        log_frame = ttk.LabelFrame(self.connection_tab, text=self.tr("log"), padding=10)
        log_frame.grid(row=1, column=0, sticky="nsew", padx=12, pady=(6, 12))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        self.log_list = tk.Listbox(log_frame, activestyle="none")
        self.log_list.grid(row=0, column=0, sticky="nsew")
        log_scroll = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_list.yview)
        log_scroll.grid(row=0, column=1, sticky="ns")
        self.log_list.configure(yscrollcommand=log_scroll.set)

        self.queue_tab.columnconfigure(0, weight=1)
        self.queue_tab.rowconfigure(1, weight=1)
        add_frame = ttk.Frame(self.queue_tab, padding=(12, 12, 12, 6))
        add_frame.grid(row=0, column=0, sticky="ew")
        add_frame.columnconfigure(0, weight=1)
        self.name_var = tk.StringVar()
        name_entry = ttk.Entry(add_frame, textvariable=self.name_var)
        name_entry.grid(row=0, column=0, sticky="ew")
        name_entry.bind("<Return>", lambda _event: self.insert_names())
        ttk.Button(add_frame, text=self.tr("insert_name"), command=self.insert_names).grid(row=0, column=1, padx=(8, 0))
        ttk.Button(add_frame, text=self.tr("append_name"), command=self.append_names).grid(row=0, column=2, padx=(8, 0))

        list_frame = ttk.Frame(self.queue_tab)
        list_frame.grid(row=1, column=0, sticky="nsew", padx=12, pady=6)
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        self.tree = ttk.Treeview(list_frame, columns=("position", "name"), show="headings", selectmode="extended")
        self.tree.heading("position", text="#")
        self.tree.heading("name", text=self.tr("viewer_name"))
        self.tree.column("position", width=55, anchor="center", stretch=False)
        self.tree.column("name", width=400, anchor="w")
        self.tree.grid(row=0, column=0, sticky="nsew")
        self.tree.bind("<ButtonPress-1>", self.start_drag_selection)
        self.tree.bind("<B1-Motion>", self.drag_selection)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)

        list_buttons = ttk.Frame(list_frame, padding=(8, 0, 0, 0))
        list_buttons.grid(row=0, column=2, sticky="n")
        ttk.Button(list_buttons, text=self.tr("move_up"), command=lambda: self.move(-1)).pack(fill="x")
        ttk.Button(list_buttons, text=self.tr("move_down"), command=lambda: self.move(1)).pack(fill="x", pady=(6, 0))
        ttk.Button(list_buttons, text=self.tr("delete"), command=self.delete).pack(fill="x", pady=(18, 0))
        ttk.Button(list_buttons, text=self.tr("clear_queue"), command=self.clear_queue).pack(fill="x", pady=(6, 0))

        controls = ttk.Frame(self.queue_tab, padding=(12, 6, 12, 12))
        controls.grid(row=2, column=0, sticky="ew")
        ttk.Label(controls, text=self.tr("people_each")).pack(side="left", padx=(0, 4))
        self.count_var = tk.IntVar(value=STATE.call_count)
        ttk.Spinbox(controls, from_=1, to=100, width=5, textvariable=self.count_var, command=self.save_count).pack(side="left")
        self.accept_queue_text = tk.StringVar(value=self.accept_queue_label())
        ttk.Button(controls, textvariable=self.accept_queue_text, command=self.toggle_accept_queue).pack(side="left", padx=(12, 0))
        ttk.Button(controls, text=self.tr("call_next"), command=self.call_next, style="CallNext.TButton").pack(side="right")
        ttk.Button(controls, text=self.tr("show_last_call"), command=self.show_last_call).pack(side="right", padx=(0, 8))
        ttk.Button(controls, text=self.tr("close_message"), command=self.close_message).pack(side="right", padx=(0, 8))
        self.show_queue_text = tk.StringVar(value=self.show_queue_label())
        ttk.Button(controls, textvariable=self.show_queue_text, command=self.show_queue).pack(side="right", padx=(0, 8))

        self.call_url = f"http://{HOST}:{STATE.port}/call"
        self.queue_url = f"http://{HOST}:{STATE.port}/queue"
        self.calendar_url = f"http://{HOST}:{STATE.port}/calendar"
        self.obs_url = self.call_url

        self.general_tab.columnconfigure(0, weight=1)
        general = ttk.LabelFrame(self.general_tab, text=self.tr("general_settings"), padding=12)
        general.grid(row=0, column=0, sticky="ew", padx=12, pady=12)
        general.columnconfigure(1, weight=1)
        ttk.Label(general, text=self.tr("language")).grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.language_var = tk.StringVar(value=LANGUAGE_NAMES.get(STATE.language, "中文"))
        ttk.Combobox(general, textvariable=self.language_var, values=list(LANGUAGES), state="readonly", width=12).grid(row=0, column=1, sticky="w")
        ttk.Label(general, text=self.tr("calendar_time_zone")).grid(row=1, column=0, sticky="w", padx=(0, 8), pady=(8, 0))
        initial_time_zone = STATE.calendar_time_zone
        initial_is_custom = initial_time_zone not in UTC_TIME_ZONE_OPTIONS
        self.calendar_time_zone_var = tk.StringVar(value=OTHER_TIME_ZONE_LABEL if initial_is_custom else initial_time_zone)
        time_zone_controls = ttk.Frame(general)
        time_zone_controls.grid(row=1, column=1, sticky="w", pady=(8, 0))
        self.calendar_time_zone_combo = ttk.Combobox(
            time_zone_controls,
            textvariable=self.calendar_time_zone_var,
            values=[
                *UTC_TIME_ZONE_OPTIONS.keys(),
                OTHER_TIME_ZONE_LABEL,
            ],
            state="readonly",
            width=24,
        )
        self.calendar_time_zone_combo.pack(side="left")
        self.calendar_time_zone_combo.bind("<<ComboboxSelected>>", lambda _event: self.update_custom_time_zone_visibility())
        self.calendar_time_zone_custom_var = tk.StringVar(value=initial_time_zone if initial_is_custom else "")
        self.calendar_time_zone_custom_frame = ttk.Frame(time_zone_controls)
        self.calendar_time_zone_custom_frame.pack(side="left", padx=(8, 0))
        ttk.Label(self.calendar_time_zone_custom_frame, text=self.tr("custom_time_zone_offset")).pack(side="left")
        ttk.Entry(self.calendar_time_zone_custom_frame, textvariable=self.calendar_time_zone_custom_var, width=8).pack(side="left", padx=(6, 0))
        ttk.Label(self.calendar_time_zone_custom_frame, text=self.tr("custom_time_zone_hint")).pack(side="left", padx=(6, 0))
        self.update_custom_time_zone_visibility()
        ttk.Label(general, text=self.tr("port")).grid(row=2, column=0, sticky="w", padx=(0, 8), pady=(8, 0))
        self.port_var = tk.IntVar(value=STATE.port)
        ttk.Spinbox(general, from_=1024, to=65535, textvariable=self.port_var, width=10).grid(row=2, column=1, sticky="w", pady=(8, 0))
        ttk.Button(general, text=self.tr("apply"), command=self.apply_settings).grid(row=3, column=1, sticky="w", pady=(12, 0))

        obs = ttk.LabelFrame(self.general_tab, text=self.tr("obs_source"), padding=12)
        obs.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 12))
        obs.columnconfigure(1, weight=1)
        for row, (label, url) in enumerate(((self.tr("call_source"), self.call_url), (self.tr("queue_source"), self.queue_url), (self.tr("calendar_source"), self.calendar_url))):
            ttk.Label(obs, text=label).grid(row=row, column=0, sticky="w", padx=(0, 8), pady=(0 if row == 0 else 6, 0))
            ttk.Label(obs, text=url).grid(row=row, column=1, sticky="w", pady=(0 if row == 0 else 6, 0))
            ttk.Button(obs, text=self.tr("copy_url"), command=lambda target=url: self.copy_url(target)).grid(row=row, column=2, padx=(8, 0), pady=(0 if row == 0 else 6, 0))
            ttk.Button(obs, text=self.tr("preview"), command=lambda target=url: webbrowser.open(target)).grid(row=row, column=3, padx=(8, 0), pady=(0 if row == 0 else 6, 0))

        self.command_tab.columnconfigure(0, weight=1)
        self.command_tab.rowconfigure(0, weight=1)
        commands_frame = ttk.Frame(self.command_tab)
        commands_frame.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)
        commands_frame.columnconfigure(0, weight=1, uniform="command_columns")
        commands_frame.columnconfigure(1, weight=1, uniform="command_columns")
        commands_frame.rowconfigure(0, weight=1, uniform="command_rows")
        commands_frame.rowconfigure(1, weight=1, uniform="command_rows")

        join_frame = ttk.LabelFrame(commands_frame, text=self.tr("join_command_title"), padding=12)
        join_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        join_frame.columnconfigure(0, weight=1)
        join_frame.rowconfigure(2, weight=1)
        self.command_var = tk.StringVar()
        command_entry = ttk.Entry(join_frame, textvariable=self.command_var)
        command_entry.grid(row=0, column=0, sticky="ew")
        command_entry.bind("<Return>", lambda _event: self.add_command("join"))
        ttk.Button(join_frame, text=self.tr("add"), command=lambda: self.add_command("join")).grid(row=0, column=1, padx=(8, 0))
        ttk.Label(join_frame, text=self.tr("join_command_hint")).grid(row=1, column=0, columnspan=2, sticky="w", pady=(8, 0))
        self.command_list = tk.Listbox(join_frame, selectmode=tk.EXTENDED, font=("", 12), activestyle="none")
        self.command_list.grid(row=2, column=0, sticky="nsew", pady=(8, 0))
        command_scroll = ttk.Scrollbar(join_frame, orient="vertical", command=self.command_list.yview)
        command_scroll.grid(row=2, column=1, sticky="ns", pady=(8, 0))
        self.command_list.configure(yscrollcommand=command_scroll.set)
        ttk.Button(join_frame, text=self.tr("delete_commands"), command=lambda: self.delete_commands("join")).grid(row=3, column=0, columnspan=2, sticky="e", pady=(10, 0))

        queue_frame = ttk.LabelFrame(commands_frame, text=self.tr("queue_command_title"), padding=12)
        queue_frame.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        queue_frame.columnconfigure(0, weight=1)
        queue_frame.rowconfigure(2, weight=1)
        self.queue_command_var = tk.StringVar()
        queue_command_entry = ttk.Entry(queue_frame, textvariable=self.queue_command_var)
        queue_command_entry.grid(row=0, column=0, sticky="ew")
        queue_command_entry.bind("<Return>", lambda _event: self.add_command("queue"))
        ttk.Button(queue_frame, text=self.tr("add"), command=lambda: self.add_command("queue")).grid(row=0, column=1, padx=(8, 0))
        ttk.Label(queue_frame, text=self.tr("queue_command_hint")).grid(row=1, column=0, columnspan=2, sticky="w", pady=(8, 0))
        self.queue_command_list = tk.Listbox(queue_frame, selectmode=tk.EXTENDED, font=("", 12), activestyle="none")
        self.queue_command_list.grid(row=2, column=0, sticky="nsew", pady=(8, 0))
        queue_command_scroll = ttk.Scrollbar(queue_frame, orient="vertical", command=self.queue_command_list.yview)
        queue_command_scroll.grid(row=2, column=1, sticky="ns", pady=(8, 0))
        self.queue_command_list.configure(yscrollcommand=queue_command_scroll.set)
        ttk.Button(queue_frame, text=self.tr("delete_commands"), command=lambda: self.delete_commands("queue")).grid(row=3, column=0, columnspan=2, sticky="e", pady=(10, 0))

        calendar_frame = ttk.LabelFrame(commands_frame, text=self.tr("calendar_command_title"), padding=12)
        calendar_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 6), pady=(12, 0))
        calendar_frame.columnconfigure(0, weight=1)
        calendar_frame.rowconfigure(2, weight=1)
        self.calendar_command_var = tk.StringVar()
        calendar_command_entry = ttk.Entry(calendar_frame, textvariable=self.calendar_command_var)
        calendar_command_entry.grid(row=0, column=0, sticky="ew")
        calendar_command_entry.bind("<Return>", lambda _event: self.add_command("calendar"))
        ttk.Button(calendar_frame, text=self.tr("add"), command=lambda: self.add_command("calendar")).grid(row=0, column=1, padx=(8, 0))
        ttk.Label(calendar_frame, text=self.tr("calendar_command_hint")).grid(row=1, column=0, columnspan=2, sticky="w", pady=(8, 0))
        self.calendar_command_list = tk.Listbox(calendar_frame, selectmode=tk.EXTENDED, font=("", 12), activestyle="none")
        self.calendar_command_list.grid(row=2, column=0, sticky="nsew", pady=(8, 0))
        calendar_command_scroll = ttk.Scrollbar(calendar_frame, orient="vertical", command=self.calendar_command_list.yview)
        calendar_command_scroll.grid(row=2, column=1, sticky="ns", pady=(8, 0))
        self.calendar_command_list.configure(yscrollcommand=calendar_command_scroll.set)
        ttk.Button(calendar_frame, text=self.tr("delete_commands"), command=lambda: self.delete_commands("calendar")).grid(row=3, column=0, columnspan=2, sticky="e", pady=(10, 0))

        blank_command_frame = ttk.Frame(commands_frame)
        blank_command_frame.grid(row=1, column=1, sticky="nsew", padx=(6, 0), pady=(12, 0))

        self.blacklist_tab.columnconfigure(0, weight=1)
        self.blacklist_tab.rowconfigure(1, weight=1)
        blacklist_add = ttk.LabelFrame(self.blacklist_tab, text=self.tr("blacklist_name"), padding=12)
        blacklist_add.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 6))
        blacklist_add.columnconfigure(1, weight=1)
        ttk.Label(blacklist_add, text=self.tr("blacklist_name")).grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.blacklist_var = tk.StringVar()
        blacklist_entry = ttk.Entry(blacklist_add, textvariable=self.blacklist_var)
        blacklist_entry.grid(row=0, column=1, sticky="ew")
        blacklist_entry.bind("<Return>", lambda _event: self.add_blacklist_name())
        ttk.Button(blacklist_add, text=self.tr("add"), command=self.add_blacklist_name).grid(row=0, column=2, padx=(8, 0))
        ttk.Label(blacklist_add, text=self.tr("blacklist_hint")).grid(row=1, column=1, columnspan=2, sticky="w", pady=(8, 0))

        blacklist_frame = ttk.LabelFrame(self.blacklist_tab, text=self.tr("current_blacklist"), padding=12)
        blacklist_frame.grid(row=1, column=0, sticky="nsew", padx=12, pady=(6, 12))
        blacklist_frame.columnconfigure(0, weight=1)
        blacklist_frame.rowconfigure(0, weight=1)
        self.blacklist_list = tk.Listbox(blacklist_frame, selectmode=tk.EXTENDED, font=("", 12), activestyle="none")
        self.blacklist_list.grid(row=0, column=0, sticky="nsew")
        blacklist_scroll = ttk.Scrollbar(blacklist_frame, orient="vertical", command=self.blacklist_list.yview)
        blacklist_scroll.grid(row=0, column=1, sticky="ns")
        self.blacklist_list.configure(yscrollcommand=blacklist_scroll.set)
        ttk.Button(blacklist_frame, text=self.tr("delete_blacklist"), command=self.delete_blacklist_names).grid(row=1, column=0, columnspan=2, sticky="e", pady=(10, 0))

        self.queue_settings_tab.columnconfigure(0, weight=1)
        queue_general = ttk.LabelFrame(self.queue_settings_tab, text=self.tr("queue_display_settings"), padding=12)
        queue_general.grid(row=0, column=0, sticky="ew", padx=12, pady=12)
        queue_general.columnconfigure(1, weight=1)
        ttk.Label(queue_general, text=self.tr("display_text")).grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.display_text_var = tk.StringVar(value=STATE.display_text)
        display_entry = ttk.Entry(queue_general, textvariable=self.display_text_var)
        display_entry.grid(row=0, column=1, columnspan=2, sticky="ew")
        display_entry.bind("<FocusOut>", lambda _event: self.save_display_text())
        display_entry.bind("<Return>", lambda _event: self.save_display_text())
        ttk.Label(queue_general, text=self.tr("name_hint")).grid(row=1, column=1, columnspan=2, sticky="w", pady=(3, 8))
        ttk.Label(queue_general, text=self.tr("display_seconds")).grid(row=2, column=0, sticky="w", padx=(0, 8), pady=(8, 0))
        self.display_seconds_var = tk.IntVar(value=STATE.display_seconds)
        ttk.Spinbox(queue_general, from_=0, to=300, textvariable=self.display_seconds_var, width=10).grid(row=2, column=1, sticky="w", pady=(8, 0))
        ttk.Label(queue_general, text=self.tr("duration_zero_hint")).grid(row=2, column=2, sticky="w", padx=(8, 0), pady=(8, 0))
        ttk.Label(queue_general, text=self.tr("queue_display_limit")).grid(row=3, column=0, sticky="w", padx=(0, 8), pady=(8, 0))
        self.queue_display_limit_var = tk.IntVar(value=STATE.queue_display_limit)
        ttk.Spinbox(queue_general, from_=1, to=100, textvariable=self.queue_display_limit_var, width=10).grid(row=3, column=1, sticky="w", pady=(8, 0))
        ttk.Label(queue_general, text=self.tr("queue_display_seconds")).grid(row=4, column=0, sticky="w", padx=(0, 8), pady=(8, 0))
        self.queue_display_seconds_var = tk.IntVar(value=STATE.queue_display_seconds)
        ttk.Spinbox(queue_general, from_=0, to=300, textvariable=self.queue_display_seconds_var, width=10).grid(row=4, column=1, sticky="w", pady=(8, 0))
        ttk.Label(queue_general, text=self.tr("duration_zero_hint")).grid(row=4, column=2, sticky="w", padx=(8, 0), pady=(8, 0))
        ttk.Button(queue_general, text=self.tr("apply"), command=self.apply_settings).grid(row=5, column=1, sticky="w", pady=(12, 0))

        sound = ttk.LabelFrame(self.queue_settings_tab, text=self.tr("sound_effect"), padding=12)
        sound.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 12))
        sound.columnconfigure(1, weight=1)
        ttk.Label(sound, text=self.tr("sound_effect")).grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.sound_var = tk.StringVar(value=STATE.sound_file or self.tr("no_sound"))
        ttk.Entry(sound, textvariable=self.sound_var, state="readonly").grid(row=0, column=1, sticky="ew")
        ttk.Button(sound, text=self.tr("browse"), command=self.browse_sound).grid(row=0, column=2, padx=(12, 0))
        ttk.Button(sound, text=self.tr("default_sound"), command=lambda: self.install_default_sound("call")).grid(row=0, column=3, padx=(8, 0))

        queue_theme = ttk.LabelFrame(self.queue_settings_tab, text=self.tr("theme_css"), padding=12)
        queue_theme.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 12))
        queue_theme.columnconfigure(1, weight=1)
        ttk.Label(queue_theme, text=self.tr("call_css")).grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.call_theme_var = tk.StringVar(value=STATE.call_css_file or self.tr("default_theme"))
        ttk.Entry(queue_theme, textvariable=self.call_theme_var, state="readonly").grid(row=0, column=1, sticky="ew")
        ttk.Button(queue_theme, text=self.tr("browse"), command=lambda: self.browse_theme("call")).grid(row=0, column=2, padx=(12, 0))
        ttk.Label(queue_theme, text=self.tr("queue_css")).grid(row=1, column=0, sticky="w", padx=(0, 8), pady=(8, 0))
        self.queue_theme_var = tk.StringVar(value=STATE.queue_css_file or self.tr("default_theme"))
        ttk.Entry(queue_theme, textvariable=self.queue_theme_var, state="readonly").grid(row=1, column=1, sticky="ew", pady=(8, 0))
        ttk.Button(queue_theme, text=self.tr("browse"), command=lambda: self.browse_theme("queue")).grid(row=1, column=2, padx=(12, 0), pady=(8, 0))

        self.calendar_settings_tab.columnconfigure(0, weight=1)
        calendar_settings = ttk.LabelFrame(self.calendar_settings_tab, text=self.tr("calendar_settings"), padding=12)
        calendar_settings.grid(row=0, column=0, sticky="ew", padx=12, pady=12)
        calendar_settings.columnconfigure(1, weight=1)
        ttk.Label(calendar_settings, text=self.tr("calendar_display_seconds")).grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.calendar_display_seconds_var = tk.IntVar(value=STATE.calendar_display_seconds)
        ttk.Spinbox(calendar_settings, from_=0, to=300, textvariable=self.calendar_display_seconds_var, width=10).grid(row=0, column=1, sticky="w")
        ttk.Label(calendar_settings, text=self.tr("duration_zero_hint")).grid(row=0, column=2, sticky="w", padx=(8, 0))
        ttk.Label(calendar_settings, text=self.tr("weekday_text")).grid(row=1, column=0, sticky="w", padx=(0, 8), pady=(8, 0))
        self.calendar_weekday_language_var = tk.StringVar(
            value=WEEKDAY_LANGUAGE_NAMES.get(STATE.calendar_weekday_language, "中")
        )
        ttk.Combobox(
            calendar_settings,
            textvariable=self.calendar_weekday_language_var,
            values=list(WEEKDAY_LANGUAGE_OPTIONS.keys()),
            state="readonly",
            width=14,
        ).grid(row=1, column=1, sticky="w", pady=(8, 0))
        ttk.Label(calendar_settings, text=self.tr("calendar_csv_prefix")).grid(row=2, column=0, sticky="w", padx=(0, 8), pady=(8, 0))
        self.calendar_csv_prefix_var = tk.StringVar(value=STATE.calendar_csv_prefix)
        ttk.Entry(calendar_settings, textvariable=self.calendar_csv_prefix_var, width=24).grid(row=2, column=1, sticky="w", pady=(8, 0))
        ttk.Label(calendar_settings, text=self.tr("calendar_css")).grid(row=3, column=0, sticky="w", padx=(0, 8), pady=(8, 0))
        self.calendar_theme_var = tk.StringVar(value=STATE.calendar_css_file or self.tr("default_theme"))
        ttk.Entry(calendar_settings, textvariable=self.calendar_theme_var, state="readonly").grid(row=3, column=1, sticky="ew", pady=(8, 0))
        ttk.Button(calendar_settings, text=self.tr("browse"), command=lambda: self.browse_theme("calendar")).grid(row=3, column=2, padx=(12, 0), pady=(8, 0))
        ttk.Label(calendar_settings, text=self.tr("sound_effect")).grid(row=4, column=0, sticky="w", padx=(0, 8), pady=(8, 0))
        self.calendar_sound_var = tk.StringVar(value=STATE.calendar_sound_file or self.tr("no_sound"))
        ttk.Entry(calendar_settings, textvariable=self.calendar_sound_var, state="readonly").grid(row=4, column=1, sticky="ew", pady=(8, 0))
        ttk.Button(calendar_settings, text=self.tr("browse"), command=lambda: self.browse_sound("calendar")).grid(row=4, column=2, padx=(12, 0), pady=(8, 0))
        ttk.Button(calendar_settings, text=self.tr("default_sound"), command=lambda: self.install_default_sound("calendar")).grid(row=4, column=3, padx=(8, 0), pady=(8, 0))
        ttk.Label(calendar_settings, text=self.tr("calendar_first_text_label")).grid(row=5, column=0, sticky="w", padx=(0, 8), pady=(8, 0))
        self.calendar_first_text_var = tk.StringVar(value=STATE.calendar_first_text)
        ttk.Entry(calendar_settings, textvariable=self.calendar_first_text_var).grid(row=5, column=1, columnspan=2, sticky="ew", pady=(8, 0))
        ttk.Label(calendar_settings, text=self.tr("calendar_checkin_text_label")).grid(row=6, column=0, sticky="w", padx=(0, 8), pady=(8, 0))
        self.calendar_checkin_text_var = tk.StringVar(value=STATE.calendar_checkin_text)
        ttk.Entry(calendar_settings, textvariable=self.calendar_checkin_text_var).grid(row=6, column=1, columnspan=2, sticky="ew", pady=(8, 0))
        ttk.Label(calendar_settings, text=self.tr("calendar_command_text_label")).grid(row=7, column=0, sticky="w", padx=(0, 8), pady=(8, 0))
        self.calendar_command_text_var = tk.StringVar(value=STATE.calendar_command_text)
        ttk.Entry(calendar_settings, textvariable=self.calendar_command_text_var).grid(row=7, column=1, columnspan=2, sticky="ew", pady=(8, 0))
        ttk.Label(calendar_settings, text=self.tr("calendar_name_variable_hint")).grid(row=8, column=1, columnspan=2, sticky="w", pady=(3, 0))
        ttk.Button(calendar_settings, text=self.tr("apply"), command=self.apply_settings).grid(row=9, column=1, sticky="w", pady=(12, 0))

        manual_calendar = ttk.LabelFrame(self.calendar_settings_tab, text=self.tr("manual_calendar_display"), padding=12)
        manual_calendar.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 12))
        manual_calendar.columnconfigure(1, weight=1)
        ttk.Label(manual_calendar, text=self.tr("manual_calendar_target")).grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.manual_calendar_target_var = tk.StringVar()
        manual_target_entry = ttk.Entry(manual_calendar, textvariable=self.manual_calendar_target_var)
        manual_target_entry.grid(row=0, column=1, sticky="ew")
        manual_target_entry.bind("<Return>", lambda _event: self.show_manual_calendar())
        ttk.Label(manual_calendar, text=self.tr("manual_calendar_month")).grid(row=0, column=2, sticky="w", padx=(12, 8))
        self.manual_calendar_month_var = tk.StringVar()
        now = STATE.calendar_now()
        month_values = [""]
        for offset in range(-12, 13):
            month_index = now.month - 1 + offset
            year = now.year + month_index // 12
            month = month_index % 12 + 1
            month_values.append(f"{year}-{month:02d}")
        manual_month_combo = ttk.Combobox(
            manual_calendar,
            textvariable=self.manual_calendar_month_var,
            values=month_values,
            width=12,
        )
        manual_month_combo.grid(row=0, column=3, sticky="w")
        manual_month_combo.bind("<Return>", lambda _event: self.show_manual_calendar())
        ttk.Button(manual_calendar, text=self.tr("manual_calendar_show"), command=self.show_manual_calendar).grid(row=0, column=4, padx=(8, 0))
        ttk.Label(manual_calendar, text=self.tr("manual_calendar_month_hint")).grid(row=1, column=1, columnspan=4, sticky="w", pady=(8, 0))

        self.refresh_commands()
        self.refresh_blacklist()
        return

        notebook = ttk.Notebook(self.root)
        notebook.grid(row=0, column=0, sticky="nsew")
        self.main_tab = ttk.Frame(notebook)
        self.command_tab = ttk.Frame(notebook)
        notebook.add(self.main_tab, text=self.tr("queue_tab"))
        notebook.add(self.command_tab, text=self.tr("settings_tab"))
        self.main_tab.columnconfigure(0, weight=1)
        self.main_tab.rowconfigure(3, weight=1)

        channel_frame = ttk.LabelFrame(self.main_tab, text=self.tr("twitch_connection"), padding=10)
        channel_frame.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 6))
        channel_frame.columnconfigure(1, weight=1)
        ttk.Label(channel_frame, text=self.tr("channel")).grid(row=0, column=0, padx=(0, 8))
        self.channel_var = tk.StringVar(value=STATE.channel)
        ttk.Entry(channel_frame, textvariable=self.channel_var).grid(row=0, column=1, sticky="ew")
        ttk.Button(channel_frame, text=self.tr("connect"), command=self.change_channel).grid(row=0, column=2, padx=(8, 0))
        self.status_var = tk.StringVar(value=self.tr("starting"))
        ttk.Label(channel_frame, textvariable=self.status_var).grid(row=1, column=0, columnspan=2, sticky="w", pady=(7, 0))
        self.accept_queue_text = tk.StringVar(value=self.accept_queue_label())
        ttk.Button(channel_frame, textvariable=self.accept_queue_text, command=self.toggle_accept_queue).grid(
            row=1, column=2, sticky="e", padx=(8, 0), pady=(7, 0)
        )
        self.action_status_var = tk.StringVar(value="")
        ttk.Label(channel_frame, textvariable=self.action_status_var).grid(row=2, column=0, columnspan=3, sticky="w", pady=(4, 0))

        obs = ttk.LabelFrame(self.main_tab, text=self.tr("obs_source"), padding=10)
        obs.grid(row=1, column=0, sticky="ew", padx=12, pady=6)
        obs.columnconfigure(1, weight=1)
        ttk.Label(obs, text=self.tr("display_text")).grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.display_text_var = tk.StringVar(value=STATE.display_text)
        display_entry = ttk.Entry(obs, textvariable=self.display_text_var)
        display_entry.grid(row=0, column=1, columnspan=2, sticky="ew")
        display_entry.bind("<FocusOut>", lambda _event: self.save_display_text())
        display_entry.bind("<Return>", lambda _event: self.save_display_text())
        ttk.Label(obs, text=self.tr("name_hint")).grid(row=1, column=1, columnspan=2, sticky="w", pady=(3, 8))
        self.call_url = f"http://{HOST}:{STATE.port}/call"
        self.queue_url = f"http://{HOST}:{STATE.port}/queue"
        self.calendar_url = f"http://{HOST}:{STATE.port}/calendar"
        self.obs_url = self.call_url
        ttk.Label(obs, text=self.tr("call_source")).grid(row=2, column=0, sticky="w", padx=(0, 8))
        ttk.Label(obs, text=self.call_url).grid(row=2, column=1, sticky="w")
        ttk.Button(obs, text=self.tr("copy_url"), command=lambda: self.copy_url(self.call_url)).grid(row=2, column=2, padx=(8, 0))
        ttk.Button(obs, text=self.tr("preview"), command=lambda: webbrowser.open(self.call_url)).grid(row=2, column=3, padx=(8, 0))
        ttk.Label(obs, text=self.tr("queue_source")).grid(row=3, column=0, sticky="w", padx=(0, 8), pady=(6, 0))
        ttk.Label(obs, text=self.queue_url).grid(row=3, column=1, sticky="w", pady=(6, 0))
        ttk.Button(obs, text=self.tr("copy_url"), command=lambda: self.copy_url(self.queue_url)).grid(row=3, column=2, padx=(8, 0), pady=(6, 0))
        ttk.Button(obs, text=self.tr("preview"), command=lambda: webbrowser.open(self.queue_url)).grid(row=3, column=3, padx=(8, 0), pady=(6, 0))
        ttk.Label(obs, text=self.tr("calendar_source")).grid(row=4, column=0, sticky="w", padx=(0, 8), pady=(6, 0))
        ttk.Label(obs, text=self.calendar_url).grid(row=4, column=1, sticky="w", pady=(6, 0))
        ttk.Button(obs, text=self.tr("copy_url"), command=lambda: self.copy_url(self.calendar_url)).grid(row=4, column=2, padx=(8, 0), pady=(6, 0))
        ttk.Button(obs, text=self.tr("preview"), command=lambda: webbrowser.open(self.calendar_url)).grid(row=4, column=3, padx=(8, 0), pady=(6, 0))

        add_frame = ttk.Frame(self.main_tab, padding=(12, 6))
        add_frame.grid(row=2, column=0, sticky="ew")
        add_frame.columnconfigure(0, weight=1)
        self.name_var = tk.StringVar()
        name_entry = ttk.Entry(add_frame, textvariable=self.name_var)
        name_entry.grid(row=0, column=0, sticky="ew")
        name_entry.bind("<Return>", lambda _event: self.insert_names())
        ttk.Button(add_frame, text=self.tr("insert_name"), command=self.insert_names).grid(row=0, column=1, padx=(8, 0))
        ttk.Button(add_frame, text=self.tr("append_name"), command=self.append_names).grid(row=0, column=2, padx=(8, 0))

        list_frame = ttk.Frame(self.main_tab)
        list_frame.grid(row=3, column=0, sticky="nsew", padx=12, pady=6)
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        self.tree = ttk.Treeview(list_frame, columns=("position", "name"), show="headings", selectmode="extended")
        self.tree.heading("position", text="#")
        self.tree.heading("name", text=self.tr("viewer_name"))
        self.tree.column("position", width=55, anchor="center", stretch=False)
        self.tree.column("name", width=400, anchor="w")
        self.tree.grid(row=0, column=0, sticky="nsew")
        self.tree.bind("<ButtonPress-1>", self.start_drag_selection)
        self.tree.bind("<B1-Motion>", self.drag_selection)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)

        list_buttons = ttk.Frame(list_frame, padding=(8, 0, 0, 0))
        list_buttons.grid(row=0, column=2, sticky="n")
        ttk.Button(list_buttons, text=self.tr("move_up"), command=lambda: self.move(-1)).pack(fill="x")
        ttk.Button(list_buttons, text=self.tr("move_down"), command=lambda: self.move(1)).pack(fill="x", pady=(6, 0))
        ttk.Button(list_buttons, text=self.tr("delete"), command=self.delete).pack(fill="x", pady=(18, 0))
        ttk.Button(list_buttons, text=self.tr("clear_queue"), command=self.clear_queue).pack(fill="x", pady=(6, 0))

        controls = ttk.Frame(self.main_tab, padding=(12, 6))
        controls.grid(row=4, column=0, sticky="ew")
        ttk.Label(controls, text=self.tr("people_each")).pack(side="left", padx=(0, 4))
        self.count_var = tk.IntVar(value=STATE.call_count)
        ttk.Spinbox(controls, from_=1, to=100, width=5, textvariable=self.count_var, command=self.save_count).pack(side="left")
        ttk.Button(
            controls, text=self.tr("call_next"), command=self.call_next, style="CallNext.TButton"
        ).pack(side="right")
        ttk.Button(controls, text=self.tr("show_last_call"), command=self.show_last_call).pack(side="right", padx=(0, 8))
        ttk.Button(controls, text=self.tr("close_message"), command=self.close_message).pack(side="right", padx=(0, 8))
        self.show_queue_text = tk.StringVar(value=self.show_queue_label())
        ttk.Button(controls, textvariable=self.show_queue_text, command=self.show_queue).pack(side="right", padx=(0, 8))

        self.command_tab.columnconfigure(0, weight=1)
        self.command_tab.rowconfigure(4, weight=1)

        general = ttk.LabelFrame(self.command_tab, text=self.tr("general_settings"), padding=12)
        general.grid(row=0, column=0, sticky="ew", padx=12, pady=12)
        general.columnconfigure(1, weight=1)
        ttk.Label(general, text=self.tr("language")).grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.language_var = tk.StringVar(value=LANGUAGE_NAMES.get(STATE.language, "銝剜?"))
        ttk.Combobox(
            general, textvariable=self.language_var, values=list(LANGUAGES), state="readonly", width=12
        ).grid(row=0, column=1, sticky="w")
        ttk.Label(general, text=self.tr("display_seconds")).grid(row=1, column=0, sticky="w", padx=(0, 8), pady=(8, 0))
        self.display_seconds_var = tk.IntVar(value=STATE.display_seconds)
        ttk.Spinbox(
            general, from_=0, to=300, textvariable=self.display_seconds_var, width=10
        ).grid(row=1, column=1, sticky="w", pady=(8, 0))
        ttk.Label(general, text=self.tr("queue_display_limit")).grid(row=2, column=0, sticky="w", padx=(0, 8), pady=(8, 0))
        self.queue_display_limit_var = tk.IntVar(value=STATE.queue_display_limit)
        ttk.Spinbox(
            general, from_=1, to=100, textvariable=self.queue_display_limit_var, width=10
        ).grid(row=2, column=1, sticky="w", pady=(8, 0))
        ttk.Label(general, text=self.tr("queue_display_seconds")).grid(row=3, column=0, sticky="w", padx=(0, 8), pady=(8, 0))
        self.queue_display_seconds_var = tk.IntVar(value=STATE.queue_display_seconds)
        ttk.Spinbox(
            general, from_=0, to=300, textvariable=self.queue_display_seconds_var, width=10
        ).grid(row=3, column=1, sticky="w", pady=(8, 0))
        ttk.Label(general, text=self.tr("calendar_display_seconds")).grid(row=4, column=0, sticky="w", padx=(0, 8), pady=(8, 0))
        self.calendar_display_seconds_var = tk.IntVar(value=STATE.calendar_display_seconds)
        ttk.Spinbox(
            general, from_=0, to=300, textvariable=self.calendar_display_seconds_var, width=10
        ).grid(row=4, column=1, sticky="w", pady=(8, 0))
        ttk.Label(general, text=self.tr("calendar_time_zone")).grid(row=5, column=0, sticky="w", padx=(0, 8), pady=(8, 0))
        self.calendar_time_zone_var = tk.StringVar(value=STATE.calendar_time_zone)
        ttk.Entry(general, textvariable=self.calendar_time_zone_var, width=24).grid(row=5, column=1, sticky="w", pady=(8, 0))
        ttk.Label(general, text=self.tr("calendar_csv_prefix")).grid(row=6, column=0, sticky="w", padx=(0, 8), pady=(8, 0))
        self.calendar_csv_prefix_var = tk.StringVar(value=STATE.calendar_csv_prefix)
        ttk.Entry(general, textvariable=self.calendar_csv_prefix_var, width=24).grid(row=6, column=1, sticky="w", pady=(8, 0))
        ttk.Label(general, text=self.tr("port")).grid(row=7, column=0, sticky="w", padx=(0, 8), pady=(8, 0))
        self.port_var = tk.IntVar(value=STATE.port)
        ttk.Spinbox(general, from_=1024, to=65535, textvariable=self.port_var, width=10).grid(
            row=7, column=1, sticky="w", pady=(8, 0)
        )
        ttk.Button(general, text=self.tr("apply"), command=self.apply_settings).grid(
            row=8, column=1, sticky="w", pady=(12, 0)
        )

        sound = ttk.LabelFrame(self.command_tab, text=self.tr("sound_effect"), padding=12)
        sound.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 12))
        sound.columnconfigure(1, weight=1)
        ttk.Label(sound, text=self.tr("sound_effect")).grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.sound_var = tk.StringVar(value=STATE.sound_file or self.tr("no_sound"))
        ttk.Entry(sound, textvariable=self.sound_var, state="readonly").grid(
            row=0, column=1, sticky="ew"
        )
        ttk.Button(sound, text=self.tr("browse"), command=self.browse_sound).grid(
            row=0, column=2, padx=(12, 0)
        )

        theme = ttk.LabelFrame(self.command_tab, text=self.tr("theme_css"), padding=12)
        theme.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 12))
        theme.columnconfigure(1, weight=1)
        ttk.Label(theme, text=self.tr("theme_css")).grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.theme_var = tk.StringVar(value=STATE.css_file or self.tr("default_theme"))
        ttk.Entry(theme, textvariable=self.theme_var, state="readonly").grid(
            row=0, column=1, sticky="ew"
        )
        ttk.Button(theme, text=self.tr("browse"), command=self.browse_theme).grid(
            row=0, column=2, padx=(12, 0)
        )

        commands_frame = ttk.Frame(self.command_tab)
        commands_frame.grid(row=3, column=0, rowspan=2, sticky="nsew", padx=12, pady=(0, 12))
        commands_frame.columnconfigure(0, weight=1)
        commands_frame.columnconfigure(1, weight=1)
        commands_frame.columnconfigure(2, weight=1)
        commands_frame.rowconfigure(0, weight=1)

        join_frame = ttk.LabelFrame(commands_frame, text=self.tr("join_command_title"), padding=12)
        join_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        join_frame.columnconfigure(0, weight=1)
        join_frame.rowconfigure(2, weight=1)
        self.command_var = tk.StringVar()
        command_entry = ttk.Entry(join_frame, textvariable=self.command_var)
        command_entry.grid(row=0, column=0, sticky="ew")
        command_entry.bind("<Return>", lambda _event: self.add_command("join"))
        ttk.Button(join_frame, text=self.tr("add"), command=lambda: self.add_command("join")).grid(row=0, column=1, padx=(8, 0))
        ttk.Label(join_frame, text=self.tr("join_command_hint")).grid(
            row=1, column=0, columnspan=2, sticky="w", pady=(8, 0)
        )
        self.command_list = tk.Listbox(join_frame, selectmode=tk.EXTENDED, font=("", 12), activestyle="none")
        self.command_list.grid(row=2, column=0, sticky="nsew", pady=(8, 0))
        command_scroll = ttk.Scrollbar(join_frame, orient="vertical", command=self.command_list.yview)
        command_scroll.grid(row=2, column=1, sticky="ns", pady=(8, 0))
        self.command_list.configure(yscrollcommand=command_scroll.set)
        ttk.Button(join_frame, text=self.tr("delete_commands"), command=lambda: self.delete_commands("join")).grid(
            row=3, column=0, columnspan=2, sticky="e", pady=(10, 0)
        )

        queue_frame = ttk.LabelFrame(commands_frame, text=self.tr("queue_command_title"), padding=12)
        queue_frame.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        queue_frame.columnconfigure(0, weight=1)
        queue_frame.rowconfigure(2, weight=1)
        self.queue_command_var = tk.StringVar()
        queue_command_entry = ttk.Entry(queue_frame, textvariable=self.queue_command_var)
        queue_command_entry.grid(row=0, column=0, sticky="ew")
        queue_command_entry.bind("<Return>", lambda _event: self.add_command("queue"))
        ttk.Button(queue_frame, text=self.tr("add"), command=lambda: self.add_command("queue")).grid(row=0, column=1, padx=(8, 0))
        ttk.Label(queue_frame, text=self.tr("queue_command_hint")).grid(
            row=1, column=0, columnspan=2, sticky="w", pady=(8, 0)
        )
        self.queue_command_list = tk.Listbox(queue_frame, selectmode=tk.EXTENDED, font=("", 12), activestyle="none")
        self.queue_command_list.grid(row=2, column=0, sticky="nsew", pady=(8, 0))
        queue_command_scroll = ttk.Scrollbar(queue_frame, orient="vertical", command=self.queue_command_list.yview)
        queue_command_scroll.grid(row=2, column=1, sticky="ns", pady=(8, 0))
        self.queue_command_list.configure(yscrollcommand=queue_command_scroll.set)
        ttk.Button(queue_frame, text=self.tr("delete_commands"), command=lambda: self.delete_commands("queue")).grid(
            row=3, column=0, columnspan=2, sticky="e", pady=(10, 0)
        )

        calendar_frame = ttk.LabelFrame(commands_frame, text=self.tr("calendar_command_title"), padding=12)
        calendar_frame.grid(row=0, column=2, sticky="nsew", padx=(6, 0))
        calendar_frame.columnconfigure(0, weight=1)
        calendar_frame.rowconfigure(2, weight=1)
        self.calendar_command_var = tk.StringVar()
        calendar_command_entry = ttk.Entry(calendar_frame, textvariable=self.calendar_command_var)
        calendar_command_entry.grid(row=0, column=0, sticky="ew")
        calendar_command_entry.bind("<Return>", lambda _event: self.add_command("calendar"))
        ttk.Button(calendar_frame, text=self.tr("add"), command=lambda: self.add_command("calendar")).grid(row=0, column=1, padx=(8, 0))
        ttk.Label(calendar_frame, text=self.tr("calendar_command_hint")).grid(
            row=1, column=0, columnspan=2, sticky="w", pady=(8, 0)
        )
        self.calendar_command_list = tk.Listbox(calendar_frame, selectmode=tk.EXTENDED, font=("", 12), activestyle="none")
        self.calendar_command_list.grid(row=2, column=0, sticky="nsew", pady=(8, 0))
        calendar_command_scroll = ttk.Scrollbar(calendar_frame, orient="vertical", command=self.calendar_command_list.yview)
        calendar_command_scroll.grid(row=2, column=1, sticky="ns", pady=(8, 0))
        self.calendar_command_list.configure(yscrollcommand=calendar_command_scroll.set)
        ttk.Button(calendar_frame, text=self.tr("delete_commands"), command=lambda: self.delete_commands("calendar")).grid(
            row=3, column=0, columnspan=2, sticky="e", pady=(10, 0)
        )
        self.refresh_commands()

    def refresh_commands(self) -> None:
        self.command_list.delete(0, tk.END)
        self.queue_command_list.delete(0, tk.END)
        self.calendar_command_list.delete(0, tk.END)
        with STATE.lock:
            commands = list(STATE.commands)
            queue_commands = list(STATE.queue_commands)
            calendar_commands = list(STATE.calendar_commands)
        for command in commands:
            self.command_list.insert(tk.END, command)
        for command in queue_commands:
            self.queue_command_list.insert(tk.END, command)
        for command in calendar_commands:
            self.calendar_command_list.insert(tk.END, command)

    def refresh_blacklist(self) -> None:
        if not hasattr(self, "blacklist_list"):
            return
        self.blacklist_list.delete(0, tk.END)
        with STATE.lock:
            blacklist_names = list(STATE.blacklist_names)
        for name in blacklist_names:
            self.blacklist_list.insert(tk.END, name)

    def update_custom_time_zone_visibility(self) -> None:
        if not hasattr(self, "calendar_time_zone_custom_frame"):
            return
        selected = self.calendar_time_zone_var.get().strip()
        if selected.casefold() == OTHER_TIME_ZONE_LABEL.casefold():
            self.calendar_time_zone_custom_frame.pack(side="left", padx=(8, 0))
        else:
            self.calendar_time_zone_custom_frame.pack_forget()

    def apply_settings(self) -> None:
        try:
            port = int(self.port_var.get())
        except (ValueError, tk.TclError):
            port = 0
        if not 1024 <= port <= 65535:
            messagebox.showerror(self.tr("invalid_port"), self.tr("invalid_port_message"))
            return
        try:
            display_seconds = int(self.display_seconds_var.get())
        except (ValueError, tk.TclError):
            display_seconds = 0
        if not 0 <= display_seconds <= 300:
            messagebox.showerror(self.tr("invalid_seconds"), self.tr("invalid_seconds_message"))
            return
        try:
            queue_display_limit = int(self.queue_display_limit_var.get())
        except (ValueError, tk.TclError):
            queue_display_limit = 0
        if not 1 <= queue_display_limit <= 100:
            messagebox.showerror(self.tr("invalid_limit"), self.tr("invalid_limit_message"))
            return
        try:
            queue_display_seconds = int(self.queue_display_seconds_var.get())
        except (ValueError, tk.TclError):
            queue_display_seconds = -1
        if not 0 <= queue_display_seconds <= 300:
            messagebox.showerror(self.tr("invalid_seconds"), self.tr("invalid_seconds_message"))
            return
        try:
            calendar_display_seconds = int(self.calendar_display_seconds_var.get())
        except (ValueError, tk.TclError):
            calendar_display_seconds = -1
        if not 0 <= calendar_display_seconds <= 300:
            messagebox.showerror(self.tr("invalid_seconds"), self.tr("invalid_seconds_message"))
            return
        selected_time_zone = self.calendar_time_zone_var.get().strip() or detect_default_time_zone_label()
        if selected_time_zone.casefold() == OTHER_TIME_ZONE_LABEL.casefold():
            calendar_time_zone = self.calendar_time_zone_custom_var.get().strip()
        else:
            calendar_time_zone = selected_time_zone
        if parse_utc_offset(calendar_time_zone) is None:
            messagebox.showerror(
                self.tr("invalid_time_zone"),
                self.tr("invalid_time_zone_message"),
            )
            return
        calendar_csv_prefix = self.calendar_csv_prefix_var.get().strip()
        calendar_weekday_language = normalize_weekday_language(
            self.calendar_weekday_language_var.get(),
            normalize_weekday_language(STATE.calendar_weekday_language, "zh"),
        )
        calendar_first_text = self.calendar_first_text_var.get().strip() or "{name}"
        calendar_checkin_text = self.calendar_checkin_text_var.get().strip() or "{name}"
        calendar_command_text = self.calendar_command_text_var.get().strip() or "{name}"
        try:
            self.server_manager.restart(port)
        except OSError as exc:
            messagebox.showerror(
                self.tr("port_error"),
                self.tr("port_error_message", port=port, error=exc),
            )
            return
        language = LANGUAGES.get(self.language_var.get(), "zh")
        with STATE.lock:
            STATE.port = port
            STATE.language = language
            STATE.display_seconds = display_seconds
            STATE.queue_display_limit = queue_display_limit
            STATE.queue_display_seconds = queue_display_seconds
            STATE.calendar_display_seconds = calendar_display_seconds
            STATE.calendar_time_zone = calendar_time_zone
            STATE.calendar_weekday_language = calendar_weekday_language
            STATE.calendar_csv_prefix = calendar_csv_prefix
            STATE.calendar_first_text = calendar_first_text
            STATE.calendar_checkin_text = calendar_checkin_text
            STATE.calendar_command_text = calendar_command_text
            STATE.refresh_queue_overlay()
            STATE.save()
        for child in self.root.winfo_children():
            child.destroy()
        self.root.title(f"{self.tr('app_title')} v{APP_VERSION}")
        self._build()
        self.refresh()
        self.set_action_status(self.tr("settings_applied", url=f"{self.call_url} / {self.queue_url} / {self.calendar_url}"))

    def browse_sound(self, area: str = "call") -> None:
        selected = filedialog.askopenfilename(
            title=self.tr("sound_effect"),
            filetypes=[
                ("Audio", "*.mp3 *.wav *.ogg *.m4a *.aac *.flac"),
                ("All files", "*.*"),
            ],
        )
        if not selected:
            return
        source = Path(selected)
        destination = AUDIO_DIR / source.name
        try:
            AUDIO_DIR.mkdir(parents=True, exist_ok=True)
            if source.resolve() != destination.resolve():
                shutil.copy2(source, destination)
        except OSError as exc:
            messagebox.showerror(self.tr("sound_copy_error"), str(exc))
            return
        with STATE.lock:
            if area == "calendar":
                STATE.calendar_sound_file = destination.name
            else:
                STATE.sound_file = destination.name
            STATE.save()
        if area == "calendar" and hasattr(self, "calendar_sound_var"):
            self.calendar_sound_var.set(destination.name)
        elif hasattr(self, "sound_var"):
            self.sound_var.set(destination.name)
        self.set_action_status(self.tr("sound_selected", name=destination.name))

    def install_default_sound(self, area: str = "call") -> None:
        if not ensure_default_audio(force=True):
            messagebox.showerror(self.tr("sound_copy_error"), "audio/default.mp3 not found")
            return
        with STATE.lock:
            if area == "calendar":
                STATE.calendar_sound_file = DEFAULT_AUDIO_FILE
            else:
                STATE.sound_file = DEFAULT_AUDIO_FILE
            STATE.save()
        if area == "calendar" and hasattr(self, "calendar_sound_var"):
            self.calendar_sound_var.set(DEFAULT_AUDIO_FILE)
        elif hasattr(self, "sound_var"):
            self.sound_var.set(DEFAULT_AUDIO_FILE)
        self.set_action_status(self.tr("default_sound_installed", name=DEFAULT_AUDIO_FILE))

    def show_manual_calendar(self) -> None:
        target = self.manual_calendar_target_var.get().strip().lstrip("@")
        if not target:
            messagebox.showerror(self.tr("calendar_command_title"), self.tr("manual_calendar_missing_target"))
            return
        month_text = self.manual_calendar_month_var.get().strip()
        date_override: tuple[int, int] | None = None
        if month_text:
            normalized = month_text.replace("/", "-")
            parts = normalized.split("-", 1)
            if len(parts) != 2:
                messagebox.showerror(self.tr("calendar_command_title"), self.tr("manual_calendar_invalid_month"))
                return
            try:
                year = int(parts[0])
                month = int(parts[1])
            except ValueError:
                messagebox.showerror(self.tr("calendar_command_title"), self.tr("manual_calendar_invalid_month"))
                return
            if not 2000 <= year <= 2099 or not 1 <= month <= 12:
                messagebox.showerror(self.tr("calendar_command_title"), self.tr("manual_calendar_invalid_month"))
                return
            date_override = (year, month)
        STATE.show_calendar(target, target, date_override, command_only=True)
        self.set_action_status(self.tr("manual_calendar_shown", name=target))

    def browse_theme(self, area: str) -> None:
        selected = filedialog.askopenfilename(
            title=self.tr("theme_css"),
            filetypes=[
                ("CSS", "*.css"),
                ("All files", "*.*"),
            ],
        )
        if not selected:
            return
        source = Path(selected)
        area_map = {
            "call": (CALL_CSS_DIR, "call_css_file", getattr(self, "call_theme_var", None)),
            "queue": (QUEUE_CSS_DIR, "queue_css_file", getattr(self, "queue_theme_var", None)),
            "calendar": (CALENDAR_CSS_DIR, "calendar_css_file", getattr(self, "calendar_theme_var", None)),
        }
        css_dir, state_attr, ui_var = area_map.get(area, area_map["call"])
        destination = css_dir / source.name
        try:
            css_dir.mkdir(parents=True, exist_ok=True)
            if source.resolve() != destination.resolve():
                shutil.copy2(source, destination)
        except OSError as exc:
            messagebox.showerror(self.tr("theme_copy_error"), str(exc))
            return
        with STATE.lock:
            setattr(STATE, state_attr, destination.name)
            STATE.save()
        if ui_var is not None:
            ui_var.set(destination.name)
        self.set_action_status(self.tr("theme_selected", name=destination.name))

    def add_command(self, command_type: str) -> None:
        if command_type == "calendar":
            target_var = self.calendar_command_var
        elif command_type == "queue":
            target_var = self.queue_command_var
        else:
            target_var = self.command_var
        command = target_var.get().strip()
        if not command:
            return
        with STATE.lock:
            if command_type == "calendar":
                target = STATE.calendar_commands
            elif command_type == "queue":
                target = STATE.queue_commands
            else:
                target = STATE.commands
            if command.casefold() in (item.casefold() for item in target):
                messagebox.showinfo(
                    self.tr("command_exists_title"),
                    self.tr("command_exists", command=command),
                )
                return
            target.append(command)
            STATE.save_commands()
        target_var.set("")
        self.refresh_commands()

    def delete_commands(self, command_type: str) -> None:
        if command_type == "calendar":
            target_list = self.calendar_command_list
        elif command_type == "queue":
            target_list = self.queue_command_list
        else:
            target_list = self.command_list
        selected = list(target_list.curselection())
        if not selected:
            return
        if not messagebox.askyesno(
            self.tr("confirm_delete"),
            self.tr("confirm_delete_commands", count=len(selected)),
            icon="warning",
        ):
            return
        with STATE.lock:
            if command_type == "calendar":
                target = STATE.calendar_commands
            elif command_type == "queue":
                target = STATE.queue_commands
            else:
                target = STATE.commands
            for index in reversed(selected):
                del target[index]
            STATE.save_commands()
        self.refresh_commands()

    def add_blacklist_name(self) -> None:
        name = self.blacklist_var.get().strip().lstrip("@")
        normalized = normalize_blacklist_name(name)
        if not normalized:
            return
        with STATE.lock:
            if normalized in (normalize_blacklist_name(item) for item in STATE.blacklist_names):
                messagebox.showinfo(
                    self.tr("blacklist_exists_title"),
                    self.tr("blacklist_exists", name=name),
                )
                return
            STATE.blacklist_names.append(name)
            STATE.save()
        self.blacklist_var.set("")
        self.refresh_blacklist()

    def delete_blacklist_names(self) -> None:
        selected = list(self.blacklist_list.curselection())
        if not selected:
            return
        if not messagebox.askyesno(
            self.tr("confirm_delete"),
            self.tr("confirm_delete_blacklist", count=len(selected)),
            icon="warning",
        ):
            return
        with STATE.lock:
            for index in reversed(selected):
                del STATE.blacklist_names[index]
            STATE.save()
        self.refresh_blacklist()

    def selected_indices(self) -> list[int]:
        return sorted(int(item) for item in self.tree.selection())

    def start_drag_selection(self, event: tk.Event) -> str | None:
        row = self.tree.identify_row(event.y)
        if not row:
            return None
        self.drag_anchor = int(row)
        ctrl_pressed = bool(event.state & 0x0004)
        shift_pressed = bool(event.state & 0x0001)
        if ctrl_pressed:
            current = set(self.tree.selection())
            if row in current:
                current.remove(row)
            else:
                current.add(row)
            self.tree.selection_set(*current)
            self.drag_base_selection = set(current)
        elif shift_pressed and self.tree.focus():
            anchor = int(self.tree.focus())
            start, end = sorted((anchor, self.drag_anchor))
            self.tree.selection_set(*(str(index) for index in range(start, end + 1)))
            self.drag_anchor = anchor
            self.drag_base_selection = set()
        else:
            self.tree.selection_set(row)
            self.drag_base_selection = set()
        self.tree.focus(row)
        return "break"

    def drag_selection(self, event: tk.Event) -> str:
        row = self.tree.identify_row(event.y)
        if not row or not hasattr(self, "drag_anchor"):
            return "break"
        current = int(row)
        start, end = sorted((self.drag_anchor, current))
        dragged = {str(index) for index in range(start, end + 1)}
        self.tree.selection_set(*(self.drag_base_selection | dragged))
        self.tree.see(row)
        return "break"

    def refresh(self, selected: list[int] | None = None) -> None:
        self.tree.delete(*self.tree.get_children())
        with STATE.lock:
            names = list(STATE.queue)
        for index, name in enumerate(names):
            self.tree.insert("", "end", iid=str(index), values=(index + 1, name))
        for index in selected or []:
            if index < len(names):
                self.tree.selection_add(str(index))

    def accept_queue_label(self) -> str:
        return self.tr("accept_queue_on" if STATE.accept_queue else "accept_queue_off")

    def toggle_accept_queue(self) -> None:
        with STATE.lock:
            STATE.accept_queue = not STATE.accept_queue
            STATE.save()
        self.accept_queue_text.set(self.accept_queue_label())

    def show_queue_label(self) -> str:
        if STATE.queue_display_seconds <= 0 and STATE.is_queue_overlay_visible():
            return self.tr("hide_queue")
        return self.tr("show_queue")

    def show_queue(self) -> None:
        if STATE.queue_display_seconds <= 0 and STATE.is_queue_overlay_visible():
            STATE.hide_queue_overlay()
            self.set_action_status(self.tr("queue_hidden"))
        else:
            STATE.show_queue_overlay()
            self.set_action_status(self.tr("queue_displayed"))
        self.show_queue_text.set(self.show_queue_label())

    def insert_names(self) -> None:
        self.add_names(append_to_end=False)

    def append_names(self) -> None:
        self.add_names(append_to_end=True)

    def add_names(self, append_to_end: bool) -> None:
        raw = self.name_var.get().strip()
        if not raw:
            return
        names = [name.strip() for name in raw.split(",") if name.strip()]
        indices = self.selected_indices()
        position = len(STATE.queue) if append_to_end or not indices else indices[0]
        with STATE.lock:
            existing = {name.casefold() for name in STATE.queue}
            new_names = [name for name in names if name.casefold() not in existing]
            STATE.queue[position:position] = new_names
            STATE.refresh_queue_overlay()
            STATE.save()
        self.name_var.set("")
        self.refresh(list(range(position, position + len(new_names))))

    def move(self, direction: int) -> None:
        selected = set(self.selected_indices())
        if not selected:
            return
        with STATE.lock:
            if direction < 0:
                for index in range(1, len(STATE.queue)):
                    if index in selected and index - 1 not in selected:
                        STATE.queue[index - 1], STATE.queue[index] = STATE.queue[index], STATE.queue[index - 1]
                        selected.remove(index)
                        selected.add(index - 1)
            else:
                for index in range(len(STATE.queue) - 2, -1, -1):
                    if index in selected and index + 1 not in selected:
                        STATE.queue[index], STATE.queue[index + 1] = STATE.queue[index + 1], STATE.queue[index]
                        selected.remove(index)
                        selected.add(index + 1)
            STATE.refresh_queue_overlay()
            STATE.save()
        self.refresh(sorted(selected))

    def delete(self) -> None:
        selected = self.selected_indices()
        if not selected:
            return
        if not messagebox.askyesno(
            self.tr("confirm_delete"),
            self.tr("confirm_delete_viewers", count=len(selected)),
            icon="warning",
        ):
            return
        with STATE.lock:
            for index in reversed(selected):
                del STATE.queue[index]
            STATE.refresh_queue_overlay()
            STATE.save()
        self.refresh()

    def clear_queue(self) -> None:
        with STATE.lock:
            count = len(STATE.queue)
        if not count:
            messagebox.showinfo(self.tr("empty_title"), self.tr("empty_message"))
            return
        if not messagebox.askyesno(
            self.tr("confirm_clear"),
            self.tr("confirm_clear_message", count=count),
            icon="warning",
        ):
            return
        with STATE.lock:
            STATE.queue.clear()
            STATE.refresh_queue_overlay()
            STATE.save()
        self.refresh()
        self.set_action_status(self.tr("queue_cleared"))

    def save_count(self) -> int:
        try:
            count = max(1, int(self.count_var.get()))
        except (ValueError, tk.TclError):
            count = 1
        self.count_var.set(count)
        with STATE.lock:
            STATE.call_count = count
            STATE.save()
        return count

    def call_next(self) -> None:
        self.save_display_text()
        names = STATE.call_next(self.save_count())
        if not names:
            messagebox.showinfo(self.tr("empty_title"), self.tr("empty_message"))
            return
        self.refresh()
        self.set_action_status(self.tr("called", names=", ".join(names)))

    def close_message(self) -> None:
        STATE.hide_call_overlay()
        self.set_action_status(self.tr("message_closed"))

    def show_last_call(self) -> None:
        if STATE.replay_last_call():
            with STATE.lock:
                names = ", ".join(STATE.last_called_names)
            self.set_action_status(self.tr("called", names=names))
        else:
            messagebox.showinfo(self.tr("empty_title"), self.tr("no_last_call"))

    def save_display_text(self) -> None:
        text = self.display_text_var.get().strip() or "輪到{name}囉"
        self.display_text_var.set(text)
        with STATE.lock:
            STATE.display_text = text
            STATE.save()

    def change_channel(self) -> None:
        channel = self.channel_var.get().strip().lstrip("#").lower()
        if not channel or any(char.isspace() for char in channel):
            messagebox.showerror(self.tr("invalid_channel"), self.tr("invalid_channel_message"))
            return
        with STATE.lock:
            STATE.channel = channel
            STATE.save()
        self.channel_var.set(channel)
        self.status_var.set(self.tr("connecting", channel=channel))
        self.chat.reconnect()

    def copy_url(self, url: str) -> None:
        self.root.clipboard_clear()
        self.root.clipboard_append(url)
        self.set_action_status(self.tr("url_copied"))

    def poll_events(self) -> None:
        try:
            while True:
                event, value = UI_EVENTS.get_nowait()
                if event == "status":
                    self.status_var.set(value)
                elif event == "queue":
                    self.refresh()
                    self.set_action_status(self.tr("viewer_joined", name=value))
                elif event == "queue_display":
                    self.set_action_status(self.tr("queue_displayed"))
                    self.show_queue_text.set(self.show_queue_label())
                elif event == "calendar":
                    self.set_action_status(self.tr("calendar_checked_in", name=value))
        except queue.Empty:
            pass
        if hasattr(self, "show_queue_text"):
            self.show_queue_text.set(self.show_queue_label())
        self.root.after(250, self.poll_events)

    def close(self) -> None:
        self.chat.stop()
        self.root.destroy()


def main() -> None:
    ensure_default_css()
    active_css_path("call")
    active_css_path("queue")
    active_css_path("calendar")
    server_manager = ServerManager(STATE.port)
    server_manager.start()
    chat = TwitchChat()
    chat.start()
    root = tk.Tk()
    App(root, chat, server_manager)
    root.mainloop()
    server_manager.stop()


if __name__ == "__main__":
    main()

