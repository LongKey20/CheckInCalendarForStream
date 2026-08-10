from __future__ import annotations

import queue
import shutil
import time
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import colorchooser, filedialog, messagebox, ttk

from .constants import (
    APP_VERSION,
    AUDIO_DIR,
    CALENDAR_CSS_DIR,
    CALENDAR_SIMPLE_FONT_SOURCE_CUSTOM,
    CALENDAR_SIMPLE_FONT_SOURCE_PRESET,
    CALENDAR_THEME_DIR,
    CALENDAR_THEME_MODE_CSS,
    CALENDAR_THEME_MODE_SIMPLE,
    CALL_CSS_DIR,
    CSS_VERSION,
    DEFAULT_AUDIO_FILE,
    DEFAULT_SIMPLE_ASPECT_RATIO_OPTIONS,
    DEFAULT_SIMPLE_FONT_OPTIONS,
    HAS_EXISTING_STATE_FILE,
    HOST,
    LOG_MAX_LINES,
    OTHER_TIME_ZONE_LABEL,
    QUEUE_CSS_DIR,
    TWITCH_AVATAR_CACHE_DIR,
    UTC_TIME_ZONE_OPTIONS,
)
from .css_manager import backup_and_migrate_css, outdated_selected_css_entries
from .i18n import (
    LANGUAGES,
    LANGUAGE_NAMES,
    WEEKDAY_LANGUAGE_NAMES,
    WEEKDAY_LANGUAGE_OPTIONS,
    normalize_weekday_language,
    translate,
)
from .resource_utils import ensure_default_audio
from .server import ServerManager
from .streaming_tools import detect_running_streaming_tools
from .time_utils import detect_default_time_zone_label, parse_utc_offset
from .twitch_chat import TwitchChat
from .utils import normalize_aspect_ratio, normalize_blacklist_name, normalize_hex_color

STATE = None
UI_EVENTS = None


def configure_ui_context(state, ui_events) -> None:
    global STATE, UI_EVENTS
    STATE = state
    UI_EVENTS = ui_events

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
        return translate(key, language=getattr(STATE, "language", "zh"), **values)

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

    def calendar_theme_mode_label(self, mode: str) -> str:
        if mode == CALENDAR_THEME_MODE_SIMPLE:
            return self.tr("calendar_theme_simple")
        return self.tr("calendar_theme_existing")

    def calendar_theme_mode_value(self) -> str:
        if getattr(self, "calendar_theme_mode_var", None) is None:
            return STATE.calendar_theme_mode
        if self.calendar_theme_mode_var.get() == CALENDAR_THEME_MODE_SIMPLE:
            return CALENDAR_THEME_MODE_SIMPLE
        return CALENDAR_THEME_MODE_CSS

    def calendar_simple_font_source_value(self) -> str:
        if getattr(self, "calendar_simple_font_source_var", None) is None:
            return STATE.calendar_simple_font_source
        if self.calendar_simple_font_source_var.get() == CALENDAR_SIMPLE_FONT_SOURCE_CUSTOM:
            return CALENDAR_SIMPLE_FONT_SOURCE_CUSTOM
        return CALENDAR_SIMPLE_FONT_SOURCE_PRESET

    def update_calendar_font_source_controls(self) -> None:
        custom_mode = self.calendar_simple_font_source_value() == CALENDAR_SIMPLE_FONT_SOURCE_CUSTOM
        if hasattr(self, "calendar_font_preset_frame"):
            if custom_mode:
                self.calendar_font_preset_frame.grid_remove()
            else:
                self.calendar_font_preset_frame.grid()
        if hasattr(self, "calendar_font_custom_frame"):
            if custom_mode:
                self.calendar_font_custom_frame.grid()
            else:
                self.calendar_font_custom_frame.grid_remove()

    def update_calendar_theme_control_states(self) -> None:
        simple_mode = self.calendar_theme_mode_value() == CALENDAR_THEME_MODE_SIMPLE
        if hasattr(self, "calendar_css_frame"):
            if simple_mode:
                self.calendar_css_frame.grid_remove()
            else:
                self.calendar_css_frame.grid()
        if hasattr(self, "calendar_simple_frame"):
            if simple_mode:
                self.calendar_simple_frame.grid()
            else:
                self.calendar_simple_frame.grid_remove()
        if simple_mode:
            self.update_calendar_font_source_controls()

    def save_calendar_theme_mode(self) -> None:
        with STATE.lock:
            new_mode = self.calendar_theme_mode_value()
            if STATE.calendar_theme_mode != new_mode:
                STATE.calendar_theme_mode = new_mode
                STATE.touch_calendar_style()
                STATE.save()
        self.update_calendar_theme_control_states()

    def save_calendar_font_source(self) -> None:
        new_source = self.calendar_simple_font_source_value()
        with STATE.lock:
            if STATE.calendar_simple_font_source != new_source:
                STATE.calendar_simple_font_source = new_source
                STATE.touch_calendar_style()
            STATE.save()
        self.update_calendar_font_source_controls()

    def choose_simple_theme_color(self, target: str) -> None:
        color_targets = {
            "text": (self.calendar_simple_text_color_var, self.calendar_simple_text_color_swatch),
            "day_bg": (self.calendar_simple_day_bg_color_var, self.calendar_simple_day_bg_color_swatch),
            "today_border": (self.calendar_simple_today_border_color_var, self.calendar_simple_today_border_color_swatch),
            "first_glow": (self.calendar_simple_first_glow_color_var, self.calendar_simple_first_glow_color_swatch),
        }
        target_var, swatch = color_targets.get(
            target,
            (self.calendar_simple_text_color_var, self.calendar_simple_text_color_swatch),
        )
        current = target_var.get()
        _rgb, color = colorchooser.askcolor(
            color=current,
            title=self.tr("choose_color"),
            parent=self.root,
        )
        if not color:
            return
        normalized = normalize_hex_color(color, current)
        target_var.set(normalized)
        swatch.configure(bg=normalized)
        self.save_simple_theme_options()

    def save_simple_theme_options(self) -> None:
        try:
            opacity = int(self.calendar_simple_day_bg_opacity_var.get())
        except (ValueError, tk.TclError):
            opacity = STATE.calendar_simple_day_bg_opacity
        opacity = min(100, max(0, opacity))
        self.calendar_simple_day_bg_opacity_var.set(opacity)
        aspect_ratio = normalize_aspect_ratio(self.calendar_simple_aspect_ratio_var.get(), STATE.calendar_simple_aspect_ratio)
        font_source = self.calendar_simple_font_source_value()
        font_family = self.calendar_simple_font_family_var.get().strip() or DEFAULT_SIMPLE_FONT_OPTIONS[0]
        self.calendar_simple_aspect_ratio_var.set(aspect_ratio)
        text_color = normalize_hex_color(self.calendar_simple_text_color_var.get(), "#ffffff")
        day_bg_color = normalize_hex_color(self.calendar_simple_day_bg_color_var.get(), "#ffffff")
        today_border_color = normalize_hex_color(self.calendar_simple_today_border_color_var.get(), "#a970ff")
        first_glow_color = normalize_hex_color(self.calendar_simple_first_glow_color_var.get(), "#ffd640")
        self.calendar_simple_font_family_var.set(font_family)
        self.calendar_simple_text_color_var.set(text_color)
        self.calendar_simple_day_bg_color_var.set(day_bg_color)
        self.calendar_simple_today_border_color_var.set(today_border_color)
        self.calendar_simple_first_glow_color_var.set(first_glow_color)
        self.calendar_simple_text_color_swatch.configure(bg=text_color)
        self.calendar_simple_day_bg_color_swatch.configure(bg=day_bg_color)
        self.calendar_simple_today_border_color_swatch.configure(bg=today_border_color)
        self.calendar_simple_first_glow_color_swatch.configure(bg=first_glow_color)
        with STATE.lock:
            changed = (
                STATE.calendar_simple_text_color != text_color
                or STATE.calendar_simple_aspect_ratio != aspect_ratio
                or STATE.calendar_simple_font_source != font_source
                or STATE.calendar_simple_font_family != font_family
                or STATE.calendar_simple_day_bg_color != day_bg_color
                or STATE.calendar_simple_day_bg_opacity != opacity
                or STATE.calendar_simple_today_border_color != today_border_color
                or STATE.calendar_simple_first_glow_color != first_glow_color
            )
            STATE.calendar_simple_aspect_ratio = aspect_ratio
            STATE.calendar_simple_font_source = font_source
            STATE.calendar_simple_font_family = font_family
            STATE.calendar_simple_text_color = text_color
            STATE.calendar_simple_day_bg_color = day_bg_color
            STATE.calendar_simple_day_bg_opacity = opacity
            STATE.calendar_simple_today_border_color = today_border_color
            STATE.calendar_simple_first_glow_color = first_glow_color
            if changed:
                STATE.touch_calendar_style()
            STATE.save()

    def show_css_version_notice_if_needed(self) -> None:
        outdated_entries = outdated_selected_css_entries(STATE)
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
        self.test_tab = ttk.Frame(notebook)
        notebook.add(self.connection_tab, text=self.tr("connection_log_tab"))
        notebook.add(self.queue_tab, text=self.tr("queue_tab"))
        notebook.add(self.general_tab, text=self.tr("general_settings"))
        notebook.add(self.command_tab, text=self.tr("command_settings_tab"))
        notebook.add(self.blacklist_tab, text=self.tr("blacklist_tab"))
        notebook.add(self.queue_settings_tab, text=self.tr("queue_settings_tab"))
        notebook.add(self.calendar_settings_tab, text=self.tr("calendar_settings"))
        notebook.add(self.test_tab, text=self.tr("test_features_tab"))

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

        self.build_test_tab()

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
        self.sound_muted_var = tk.BooleanVar(value=STATE.sound_muted)
        ttk.Checkbutton(sound, text=self.tr("mute_sound"), variable=self.sound_muted_var, command=self.save_sound_mute).grid(
            row=0, column=4, padx=(12, 0)
        )

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
            value=WEEKDAY_LANGUAGE_NAMES.get(STATE.calendar_weekday_language, next(iter(WEEKDAY_LANGUAGE_OPTIONS)))
        )
        ttk.Combobox(
            calendar_settings,
            textvariable=self.calendar_weekday_language_var,
            values=list(WEEKDAY_LANGUAGE_OPTIONS.keys()),
            state="readonly",
            width=42,
        ).grid(row=1, column=1, sticky="w", pady=(8, 0))
        ttk.Label(calendar_settings, text=self.tr("calendar_csv_prefix")).grid(row=2, column=0, sticky="w", padx=(0, 8), pady=(8, 0))
        self.calendar_csv_prefix_var = tk.StringVar(value=STATE.calendar_csv_prefix)
        ttk.Entry(calendar_settings, textvariable=self.calendar_csv_prefix_var, width=24).grid(row=2, column=1, sticky="w", pady=(8, 0))
        ttk.Label(calendar_settings, text=self.tr("calendar_theme_mode")).grid(row=3, column=0, sticky="w", padx=(0, 8), pady=(8, 0))
        self.calendar_theme_mode_var = tk.StringVar(value=STATE.calendar_theme_mode)
        theme_mode_frame = ttk.Frame(calendar_settings)
        theme_mode_frame.grid(row=3, column=1, columnspan=3, sticky="w", pady=(8, 0))
        ttk.Radiobutton(
            theme_mode_frame,
            text=self.tr("calendar_theme_existing"),
            variable=self.calendar_theme_mode_var,
            value=CALENDAR_THEME_MODE_CSS,
            command=self.save_calendar_theme_mode,
        ).grid(row=0, column=0, sticky="w")
        ttk.Radiobutton(
            theme_mode_frame,
            text=self.tr("calendar_theme_simple"),
            variable=self.calendar_theme_mode_var,
            value=CALENDAR_THEME_MODE_SIMPLE,
            command=self.save_calendar_theme_mode,
        ).grid(row=0, column=1, sticky="w", padx=(16, 0))
        self.calendar_css_frame = ttk.LabelFrame(calendar_settings, text=self.tr("calendar_theme_existing"), padding=8)
        self.calendar_css_frame.grid(row=4, column=0, columnspan=5, sticky="ew", pady=(8, 0))
        self.calendar_css_frame.columnconfigure(1, weight=1)
        ttk.Label(self.calendar_css_frame, text=self.tr("calendar_css")).grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.calendar_theme_var = tk.StringVar(value=STATE.calendar_css_file or self.tr("default_theme"))
        self.calendar_theme_entry = ttk.Entry(self.calendar_css_frame, textvariable=self.calendar_theme_var, state="readonly")
        self.calendar_theme_entry.grid(row=0, column=1, sticky="ew")
        self.calendar_theme_button = ttk.Button(self.calendar_css_frame, text=self.tr("browse"), command=lambda: self.browse_theme("calendar"))
        self.calendar_theme_button.grid(row=0, column=2, padx=(12, 0))
        self.calendar_simple_frame = ttk.LabelFrame(calendar_settings, text=self.tr("calendar_theme_simple"), padding=8)
        self.calendar_simple_frame.grid(row=5, column=0, columnspan=5, sticky="ew", pady=(8, 0))
        self.calendar_simple_frame.columnconfigure(1, weight=0)
        self.calendar_simple_frame.columnconfigure(2, weight=1)
        ttk.Label(self.calendar_simple_frame, text=self.tr("calendar_background_image")).grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.calendar_background_var = tk.StringVar(value=STATE.calendar_background_image or self.tr("no_image"))
        self.calendar_background_entry = ttk.Entry(self.calendar_simple_frame, textvariable=self.calendar_background_var, state="readonly")
        self.calendar_background_entry.grid(row=0, column=1, columnspan=2, sticky="ew")
        self.calendar_background_button = ttk.Button(self.calendar_simple_frame, text=self.tr("browse"), command=self.browse_calendar_background)
        self.calendar_background_button.grid(row=0, column=3, padx=(12, 0))
        self.calendar_background_clear_button = ttk.Button(self.calendar_simple_frame, text=self.tr("clear_background"), command=self.clear_calendar_background)
        self.calendar_background_clear_button.grid(row=0, column=4, padx=(8, 0))
        ttk.Label(self.calendar_simple_frame, text=self.tr("calendar_simple_aspect_ratio")).grid(row=1, column=0, sticky="w", padx=(0, 8), pady=(8, 0))
        self.calendar_simple_aspect_ratio_var = tk.StringVar(value=STATE.calendar_simple_aspect_ratio)
        self.calendar_simple_aspect_ratio_combo = ttk.Combobox(
            self.calendar_simple_frame,
            textvariable=self.calendar_simple_aspect_ratio_var,
            values=DEFAULT_SIMPLE_ASPECT_RATIO_OPTIONS,
            width=12,
        )
        self.calendar_simple_aspect_ratio_combo.grid(row=1, column=1, sticky="w", pady=(8, 0))
        self.calendar_simple_aspect_ratio_combo.bind("<<ComboboxSelected>>", lambda _event: self.save_simple_theme_options())
        self.calendar_simple_aspect_ratio_combo.bind("<FocusOut>", lambda _event: self.save_simple_theme_options())
        self.calendar_simple_aspect_ratio_combo.bind("<Return>", lambda _event: self.save_simple_theme_options())
        ttk.Label(self.calendar_simple_frame, text=self.tr("calendar_simple_font_source")).grid(row=2, column=0, sticky="w", padx=(0, 8), pady=(8, 0))
        self.calendar_simple_font_source_var = tk.StringVar(value=STATE.calendar_simple_font_source)
        font_source_frame = ttk.Frame(self.calendar_simple_frame)
        font_source_frame.grid(row=2, column=1, sticky="w", padx=(0, 18), pady=(8, 0))
        ttk.Radiobutton(
            font_source_frame,
            text=self.tr("calendar_simple_font_preset"),
            variable=self.calendar_simple_font_source_var,
            value=CALENDAR_SIMPLE_FONT_SOURCE_PRESET,
            command=self.save_calendar_font_source,
        ).grid(row=0, column=0, sticky="w")
        ttk.Radiobutton(
            font_source_frame,
            text=self.tr("calendar_simple_font_custom"),
            variable=self.calendar_simple_font_source_var,
            value=CALENDAR_SIMPLE_FONT_SOURCE_CUSTOM,
            command=self.save_calendar_font_source,
        ).grid(row=0, column=1, sticky="w", padx=(12, 0))
        self.calendar_font_preset_frame = ttk.Frame(self.calendar_simple_frame)
        self.calendar_font_preset_frame.grid(row=2, column=2, columnspan=3, sticky="ew", pady=(8, 0))
        self.calendar_font_preset_frame.columnconfigure(0, weight=1)
        self.calendar_simple_font_family_var = tk.StringVar(value=STATE.calendar_simple_font_family)
        self.calendar_simple_font_combo = ttk.Combobox(
            self.calendar_font_preset_frame,
            textvariable=self.calendar_simple_font_family_var,
            values=DEFAULT_SIMPLE_FONT_OPTIONS,
            width=28,
        )
        self.calendar_simple_font_combo.grid(row=0, column=0, sticky="ew")
        self.calendar_simple_font_combo.bind("<<ComboboxSelected>>", lambda _event: self.save_simple_theme_options())
        self.calendar_simple_font_combo.bind("<FocusOut>", lambda _event: self.save_simple_theme_options())
        self.calendar_simple_font_combo.bind("<Return>", lambda _event: self.save_simple_theme_options())
        self.calendar_font_custom_frame = ttk.Frame(self.calendar_simple_frame)
        self.calendar_font_custom_frame.grid(row=2, column=2, columnspan=3, sticky="ew", pady=(8, 0))
        self.calendar_font_custom_frame.columnconfigure(0, weight=1)
        self.calendar_simple_font_file_var = tk.StringVar(value=STATE.calendar_simple_font_file or self.tr("no_font"))
        self.calendar_simple_font_file_entry = ttk.Entry(self.calendar_font_custom_frame, textvariable=self.calendar_simple_font_file_var, state="readonly")
        self.calendar_simple_font_file_entry.grid(row=0, column=0, sticky="ew")
        self.calendar_simple_font_button = ttk.Button(self.calendar_font_custom_frame, text=self.tr("browse"), command=self.browse_calendar_font)
        self.calendar_simple_font_button.grid(row=0, column=1, padx=(12, 0))
        self.calendar_simple_font_clear_button = ttk.Button(self.calendar_font_custom_frame, text=self.tr("clear_font"), command=self.clear_calendar_font)
        self.calendar_simple_font_clear_button.grid(row=0, column=2, padx=(8, 0))
        colors_frame = ttk.Frame(self.calendar_simple_frame)
        colors_frame.grid(row=3, column=0, columnspan=5, sticky="ew", pady=(8, 0))
        colors_frame.columnconfigure(1, weight=1)
        colors_frame.columnconfigure(4, weight=1)
        ttk.Label(colors_frame, text=self.tr("calendar_simple_text_color")).grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.calendar_simple_text_color_var = tk.StringVar(value=STATE.calendar_simple_text_color)
        self.calendar_simple_text_color_swatch = tk.Label(colors_frame, width=4, relief="solid", bg=STATE.calendar_simple_text_color)
        self.calendar_simple_text_color_swatch.grid(row=0, column=1, sticky="w")
        self.calendar_simple_text_color_button = ttk.Button(
            colors_frame,
            text=self.tr("choose_color"),
            command=lambda: self.choose_simple_theme_color("text"),
        )
        self.calendar_simple_text_color_button.grid(row=0, column=2, padx=(8, 18))
        ttk.Label(colors_frame, text=self.tr("calendar_simple_day_bg_color")).grid(row=0, column=3, sticky="w", padx=(0, 8))
        self.calendar_simple_day_bg_color_var = tk.StringVar(value=STATE.calendar_simple_day_bg_color)
        self.calendar_simple_day_bg_color_swatch = tk.Label(colors_frame, width=4, relief="solid", bg=STATE.calendar_simple_day_bg_color)
        self.calendar_simple_day_bg_color_swatch.grid(row=0, column=4, sticky="w")
        self.calendar_simple_day_bg_color_button = ttk.Button(
            colors_frame,
            text=self.tr("choose_color"),
            command=lambda: self.choose_simple_theme_color("day_bg"),
        )
        self.calendar_simple_day_bg_color_button.grid(row=0, column=5, padx=(8, 8))
        ttk.Label(colors_frame, text=self.tr("calendar_simple_day_bg_opacity")).grid(row=0, column=6, sticky="w", padx=(0, 8))
        self.calendar_simple_day_bg_opacity_var = tk.IntVar(value=STATE.calendar_simple_day_bg_opacity)
        self.calendar_simple_day_bg_opacity_spinbox = ttk.Spinbox(
            colors_frame,
            from_=0,
            to=100,
            textvariable=self.calendar_simple_day_bg_opacity_var,
            width=6,
            command=self.save_simple_theme_options,
        )
        self.calendar_simple_day_bg_opacity_spinbox.grid(row=0, column=7, sticky="w")
        self.calendar_simple_day_bg_opacity_spinbox.bind("<FocusOut>", lambda _event: self.save_simple_theme_options())
        self.calendar_simple_day_bg_opacity_spinbox.bind("<Return>", lambda _event: self.save_simple_theme_options())
        ttk.Label(colors_frame, text=self.tr("calendar_simple_today_border_color")).grid(row=1, column=0, sticky="w", padx=(0, 8), pady=(8, 0))
        self.calendar_simple_today_border_color_var = tk.StringVar(value=STATE.calendar_simple_today_border_color)
        self.calendar_simple_today_border_color_swatch = tk.Label(colors_frame, width=4, relief="solid", bg=STATE.calendar_simple_today_border_color)
        self.calendar_simple_today_border_color_swatch.grid(row=1, column=1, sticky="w", pady=(8, 0))
        self.calendar_simple_today_border_color_button = ttk.Button(
            colors_frame,
            text=self.tr("choose_color"),
            command=lambda: self.choose_simple_theme_color("today_border"),
        )
        self.calendar_simple_today_border_color_button.grid(row=1, column=2, padx=(8, 18), pady=(8, 0))
        ttk.Label(colors_frame, text=self.tr("calendar_simple_first_glow_color")).grid(row=1, column=3, sticky="w", padx=(0, 8), pady=(8, 0))
        self.calendar_simple_first_glow_color_var = tk.StringVar(value=STATE.calendar_simple_first_glow_color)
        self.calendar_simple_first_glow_color_swatch = tk.Label(colors_frame, width=4, relief="solid", bg=STATE.calendar_simple_first_glow_color)
        self.calendar_simple_first_glow_color_swatch.grid(row=1, column=4, sticky="w", pady=(8, 0))
        self.calendar_simple_first_glow_color_button = ttk.Button(
            colors_frame,
            text=self.tr("choose_color"),
            command=lambda: self.choose_simple_theme_color("first_glow"),
        )
        self.calendar_simple_first_glow_color_button.grid(row=1, column=5, padx=(8, 8), pady=(8, 0))
        self.update_calendar_theme_control_states()
        ttk.Label(calendar_settings, text=self.tr("sound_effect")).grid(row=6, column=0, sticky="w", padx=(0, 8), pady=(8, 0))
        self.calendar_sound_var = tk.StringVar(value=STATE.calendar_sound_file or self.tr("no_sound"))
        ttk.Entry(calendar_settings, textvariable=self.calendar_sound_var, state="readonly").grid(row=6, column=1, sticky="ew", pady=(8, 0))
        ttk.Button(calendar_settings, text=self.tr("browse"), command=lambda: self.browse_sound("calendar")).grid(row=6, column=2, padx=(12, 0), pady=(8, 0))
        ttk.Button(calendar_settings, text=self.tr("default_sound"), command=lambda: self.install_default_sound("calendar")).grid(row=6, column=3, padx=(8, 0), pady=(8, 0))
        self.calendar_sound_muted_var = tk.BooleanVar(value=STATE.calendar_sound_muted)
        ttk.Checkbutton(
            calendar_settings,
            text=self.tr("mute_sound"),
            variable=self.calendar_sound_muted_var,
            command=self.save_sound_mute,
        ).grid(row=6, column=4, padx=(12, 0), pady=(8, 0))
        ttk.Label(calendar_settings, text=self.tr("calendar_first_text_label")).grid(row=7, column=0, sticky="w", padx=(0, 8), pady=(8, 0))
        self.calendar_first_text_var = tk.StringVar(value=STATE.calendar_first_text)
        ttk.Entry(calendar_settings, textvariable=self.calendar_first_text_var).grid(row=7, column=1, columnspan=2, sticky="ew", pady=(8, 0))
        ttk.Label(calendar_settings, text=self.tr("calendar_checkin_text_label")).grid(row=8, column=0, sticky="w", padx=(0, 8), pady=(8, 0))
        self.calendar_checkin_text_var = tk.StringVar(value=STATE.calendar_checkin_text)
        ttk.Entry(calendar_settings, textvariable=self.calendar_checkin_text_var).grid(row=8, column=1, columnspan=2, sticky="ew", pady=(8, 0))
        ttk.Label(calendar_settings, text=self.tr("calendar_command_text_label")).grid(row=9, column=0, sticky="w", padx=(0, 8), pady=(8, 0))
        self.calendar_command_text_var = tk.StringVar(value=STATE.calendar_command_text)
        ttk.Entry(calendar_settings, textvariable=self.calendar_command_text_var).grid(row=9, column=1, columnspan=2, sticky="ew", pady=(8, 0))
        ttk.Label(calendar_settings, text=self.tr("calendar_name_variable_hint")).grid(row=10, column=1, columnspan=2, sticky="w", pady=(3, 0))
        ttk.Button(calendar_settings, text=self.tr("apply"), command=self.apply_settings).grid(row=11, column=1, sticky="w", pady=(12, 0))

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
        self.language_var = tk.StringVar(value=LANGUAGE_NAMES.get(STATE.language, "中文"))
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

    def build_test_tab(self) -> None:
        self.test_tab.columnconfigure(0, weight=1)
        settings = ttk.LabelFrame(self.test_tab, text=self.tr("avatar_cache_settings"), padding=12)
        settings.grid(row=0, column=0, sticky="ew", padx=12, pady=12)
        settings.columnconfigure(1, weight=1)
        ttk.Label(settings, text=self.tr("avatar_cache_days")).grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.avatar_cache_days_var = tk.IntVar(value=STATE.avatar_cache_days)
        ttk.Spinbox(settings, from_=0, to=365, textvariable=self.avatar_cache_days_var, width=10).grid(
            row=0, column=1, sticky="w"
        )
        ttk.Button(settings, text=self.tr("apply"), command=self.apply_test_settings).grid(
            row=0, column=2, padx=(12, 0)
        )
        ttk.Label(settings, text=self.tr("avatar_cache_days_hint")).grid(
            row=1, column=1, columnspan=2, sticky="w", pady=(6, 0)
        )
        ttk.Label(settings, text=f"{self.tr('avatar_cache_location')}: {TWITCH_AVATAR_CACHE_DIR}").grid(
            row=2, column=1, columnspan=2, sticky="w", pady=(6, 0)
        )
        ttk.Label(
            self.test_tab,
            text=self.tr("avatar_cache_description"),
            wraplength=820,
            justify="left",
        ).grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 12))

    def apply_test_settings(self) -> None:
        try:
            cache_days = int(self.avatar_cache_days_var.get())
        except (ValueError, tk.TclError):
            cache_days = -1
        if not 0 <= cache_days <= 365:
            messagebox.showerror(
                self.tr("invalid_avatar_cache_days"),
                self.tr("invalid_avatar_cache_days_message"),
                parent=self.root,
            )
            return
        self.avatar_cache_days_var.set(cache_days)
        with STATE.lock:
            STATE.avatar_cache_days = cache_days
            STATE.save()
        self.set_action_status(self.tr("avatar_cache_applied", days=cache_days))

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
        calendar_theme_mode = self.calendar_theme_mode_value()
        self.save_simple_theme_options()
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
            old_calendar_theme_mode = STATE.calendar_theme_mode
            STATE.port = port
            STATE.language = language
            STATE.display_seconds = display_seconds
            STATE.queue_display_limit = queue_display_limit
            STATE.queue_display_seconds = queue_display_seconds
            STATE.calendar_display_seconds = calendar_display_seconds
            if hasattr(self, "sound_muted_var"):
                STATE.sound_muted = bool(self.sound_muted_var.get())
            if hasattr(self, "calendar_sound_muted_var"):
                STATE.calendar_sound_muted = bool(self.calendar_sound_muted_var.get())
            STATE.calendar_time_zone = calendar_time_zone
            STATE.calendar_weekday_language = calendar_weekday_language
            STATE.calendar_csv_prefix = calendar_csv_prefix
            STATE.calendar_first_text = calendar_first_text
            STATE.calendar_checkin_text = calendar_checkin_text
            STATE.calendar_command_text = calendar_command_text
            STATE.calendar_theme_mode = calendar_theme_mode
            if STATE.calendar_theme_mode != old_calendar_theme_mode:
                STATE.touch_calendar_style()
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

    def browse_calendar_background(self) -> None:
        selected = filedialog.askopenfilename(
            title=self.tr("calendar_background_image"),
            filetypes=[
                ("Image", "*.png *.jpg *.jpeg *.webp *.gif"),
                ("All files", "*.*"),
            ],
        )
        if not selected:
            return
        source = Path(selected)
        destination = CALENDAR_THEME_DIR / source.name
        try:
            CALENDAR_THEME_DIR.mkdir(parents=True, exist_ok=True)
            if source.resolve() != destination.resolve():
                shutil.copy2(source, destination)
        except OSError as exc:
            messagebox.showerror(self.tr("image_copy_error"), str(exc))
            return
        with STATE.lock:
            STATE.calendar_background_image = destination.name
            STATE.touch_calendar_style()
            STATE.save()
        if hasattr(self, "calendar_background_var"):
            self.calendar_background_var.set(destination.name)
        self.set_action_status(self.tr("image_selected", name=destination.name))

    def clear_calendar_background(self) -> None:
        with STATE.lock:
            STATE.calendar_background_image = ""
            STATE.touch_calendar_style()
            STATE.save()
        if hasattr(self, "calendar_background_var"):
            self.calendar_background_var.set(self.tr("no_image"))

    def browse_calendar_font(self) -> None:
        selected = filedialog.askopenfilename(
            title=self.tr("calendar_simple_custom_font"),
            filetypes=[
                ("Font", "*.ttf *.otf *.woff *.woff2"),
                ("All files", "*.*"),
            ],
        )
        if not selected:
            return
        source = Path(selected)
        destination = CALENDAR_THEME_DIR / source.name
        try:
            CALENDAR_THEME_DIR.mkdir(parents=True, exist_ok=True)
            if source.resolve() != destination.resolve():
                shutil.copy2(source, destination)
        except OSError as exc:
            messagebox.showerror(self.tr("font_copy_error"), str(exc))
            return
        with STATE.lock:
            STATE.calendar_simple_font_source = CALENDAR_SIMPLE_FONT_SOURCE_CUSTOM
            STATE.calendar_simple_font_file = destination.name
            STATE.touch_calendar_style()
            STATE.save()
        if hasattr(self, "calendar_simple_font_source_var"):
            self.calendar_simple_font_source_var.set(CALENDAR_SIMPLE_FONT_SOURCE_CUSTOM)
            self.update_calendar_font_source_controls()
        if hasattr(self, "calendar_simple_font_file_var"):
            self.calendar_simple_font_file_var.set(destination.name)
        self.set_action_status(self.tr("font_selected", name=destination.name))

    def clear_calendar_font(self) -> None:
        with STATE.lock:
            STATE.calendar_simple_font_source = CALENDAR_SIMPLE_FONT_SOURCE_PRESET
            STATE.calendar_simple_font_file = ""
            STATE.touch_calendar_style()
            STATE.save()
        if hasattr(self, "calendar_simple_font_source_var"):
            self.calendar_simple_font_source_var.set(CALENDAR_SIMPLE_FONT_SOURCE_PRESET)
            self.update_calendar_font_source_controls()
        if hasattr(self, "calendar_simple_font_file_var"):
            self.calendar_simple_font_file_var.set(self.tr("no_font"))

    def save_sound_mute(self) -> None:
        with STATE.lock:
            if hasattr(self, "sound_muted_var"):
                STATE.sound_muted = bool(self.sound_muted_var.get())
            if hasattr(self, "calendar_sound_muted_var"):
                STATE.calendar_sound_muted = bool(self.calendar_sound_muted_var.get())
            STATE.save()

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
        name = self.chat.enqueue_manual_calendar(target, date_override)
        self.set_action_status(self.tr("manual_calendar_shown", name=name or target))

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
            if area == "calendar":
                STATE.touch_calendar_style()
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
                elif event == "calendar_display":
                    self.set_action_status(self.tr("calendar_displayed"))
        except queue.Empty:
            pass
        if hasattr(self, "show_queue_text"):
            self.show_queue_text.set(self.show_queue_label())
        self.root.after(250, self.poll_events)

    def close(self) -> None:
        self.chat.stop()
        self.root.destroy()


