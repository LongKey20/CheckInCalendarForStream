from __future__ import annotations

import json
import mimetypes
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from .constants import HOST
from .css_manager import (
    active_calendar_background_path,
    active_calendar_font_path,
    active_css_path,
    calendar_css_response,
)
from .overlay_html import CALL_OVERLAY_HTML, CALENDAR_OVERLAY_HTML, QUEUE_OVERLAY_HTML
from .resource_utils import active_audio_path


class OverlayHandler(BaseHTTPRequestHandler):
    state = None

    def do_GET(self) -> None:
        state = self.state
        if state is None:
            self.send_error(503)
            return
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
            state.expire_overlays()
            with state.lock:
                payload = dict(state.overlay_event)
                payload["calendar_style_version"] = state.calendar_style_version
                body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            content_type = "application/json; charset=utf-8"
        elif path in ("/default.css", "/css/call/default.css"):
            try:
                body = active_css_path(state, "call").read_bytes()
            except FileNotFoundError:
                self.send_error(404)
                return
            content_type = "text/css; charset=utf-8"
        elif path == "/css/queue/default.css":
            try:
                body = active_css_path(state, "queue").read_bytes()
            except FileNotFoundError:
                self.send_error(404)
                return
            content_type = "text/css; charset=utf-8"
        elif path == "/css/calendar/default.css":
            try:
                body = calendar_css_response(state)
            except FileNotFoundError:
                self.send_error(404)
                return
            content_type = "text/css; charset=utf-8"
        elif path == "/calendar/simple-background":
            image_path = active_calendar_background_path(state)
            if not image_path:
                self.send_error(404)
                return
            try:
                body = image_path.read_bytes()
            except OSError:
                self.send_error(404)
                return
            content_type = mimetypes.guess_type(image_path.name)[0] or "application/octet-stream"
        elif path == "/calendar/simple-font":
            font_path = active_calendar_font_path(state)
            if not font_path:
                self.send_error(404)
                return
            try:
                body = font_path.read_bytes()
            except OSError:
                self.send_error(404)
                return
            content_type = mimetypes.guess_type(font_path.name)[0] or "font/ttf"
        elif path.startswith("/avatar/"):
            username = path.rsplit("/", 1)[-1]
            resource = state.avatar_cache.resource(username)
            if not resource:
                self.send_error(404)
                return
            body = resource.body
            content_type = resource.content_type
        elif path in ("/sound", "/audio/call", "/audio/calendar"):
            with state.lock:
                sound_file = state.calendar_sound_file if path == "/audio/calendar" else state.sound_file
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
    def __init__(self, port: int, state) -> None:
        self.server: ThreadingHTTPServer | None = None
        self.thread: threading.Thread | None = None
        self.port = port
        self.state = state

    def start(self) -> None:
        OverlayHandler.state = self.state
        self.server = ThreadingHTTPServer((HOST, self.port), OverlayHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def restart(self, port: int) -> None:
        if port == self.port:
            return
        OverlayHandler.state = self.state
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
