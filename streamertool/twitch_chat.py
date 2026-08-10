from __future__ import annotations

import base64
import hashlib
import queue
import secrets
import socket
import ssl
import struct
import threading
import time
from dataclasses import dataclass

from .constants import CHAT_IDLE_TIMEOUT_SECONDS
from .i18n import translate


@dataclass
class CalendarJob:
    username: str
    display_name: str
    visible_name: str
    date_override: tuple[int, int] | None
    command_only: bool


class TwitchChat(threading.Thread):
    def __init__(self, state, ui_events) -> None:
        super().__init__(daemon=True)
        self.state = state
        self.ui_events = ui_events
        self.stop_event = threading.Event()
        self.reconnect_event = threading.Event()
        self.calendar_jobs: queue.Queue[CalendarJob | None] = queue.Queue()
        self.calendar_worker = threading.Thread(target=self._calendar_worker_loop, daemon=True)
        self.calendar_worker.start()

    def reconnect(self) -> None:
        self.reconnect_event.set()

    def stop(self) -> None:
        self.stop_event.set()
        self.reconnect_event.set()
        self.calendar_jobs.put(None)

    def tr(self, key: str, **values) -> str:
        return translate(key, language=getattr(self.state, "language", "zh"), **values)

    def enqueue_calendar(
        self,
        username: str,
        display_name: str,
        visible_name: str,
        date_override: tuple[int, int] | None,
        command_only: bool,
    ) -> None:
        self.calendar_jobs.put(CalendarJob(username, display_name, visible_name, date_override, command_only))

    def enqueue_manual_calendar(
        self,
        target: str,
        date_override: tuple[int, int] | None = None,
    ) -> str:
        username, display_name = self.state.resolve_calendar_identity(target, date_override)
        visible_name = display_name or username or target
        if username:
            self.enqueue_calendar(username, visible_name, visible_name, date_override, True)
        return visible_name

    def _calendar_worker_loop(self) -> None:
        while not self.stop_event.is_set():
            job = self.calendar_jobs.get()
            try:
                if job is None:
                    return
                try:
                    shown = self.state.show_calendar(
                        job.username,
                        job.display_name,
                        job.date_override,
                        job.command_only,
                    )
                except Exception as exc:
                    self.ui_events.put(("status", self.tr("calendar_error", error=exc)))
                    shown = False
                if shown:
                    if job.command_only:
                        self.ui_events.put(("calendar_display", job.visible_name))
                    else:
                        self.ui_events.put(("calendar", job.visible_name))
            finally:
                self.calendar_jobs.task_done()

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
        self.ui_events.put(("status", self.tr("connected", channel=channel)))
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

    def _handle_line(self, line: str) -> None:
        if " PRIVMSG #" not in line:
            return
        prefix, _, message = line.partition(" PRIVMSG #")
        _, _, text = message.partition(" :")
        _tags, login, display_name = TwitchChat._parse_twitch_sender(prefix)
        if not login:
            return
        with self.state.lock:
            is_blacklisted = self.state.is_blacklisted(login, display_name)
        if is_blacklisted:
            return
        command = text.strip().casefold()
        with self.state.lock:
            join_matches = {item.casefold() for item in self.state.commands}
            queue_matches = {item.casefold() for item in self.state.queue_commands}
            calendar_commands = list(self.state.calendar_commands)
        is_join_command = command in join_matches
        is_queue_command = command in queue_matches
        is_calendar_command, calendar_override = TwitchChat._parse_calendar_command(text, calendar_commands)
        if is_queue_command:
            self.state.show_queue_overlay()
            self.ui_events.put(("queue_display", ""))
        if display_name and login and display_name.casefold() != login.casefold():
            name = f"{display_name}({login})"
        else:
            name = display_name or login
        self.state.remember_user(login, display_name or login)
        is_any_command = is_join_command or is_queue_command or is_calendar_command
        if login and name and (is_calendar_command or not is_any_command):
            self.enqueue_calendar(login, display_name or login, name, calendar_override, is_any_command)
        if is_join_command and name and self.state.add_viewer(name):
            self.ui_events.put(("queue", name))

    def run(self) -> None:
        while not self.stop_event.is_set():
            self.reconnect_event.clear()
            with self.state.lock:
                channel = self.state.channel
            if not channel:
                self.ui_events.put(("status", self.tr("enter_channel")))
                self.reconnect_event.wait(1)
                continue
            try:
                self._connect(channel)
            except Exception as exc:
                if not self.stop_event.is_set() and not self.reconnect_event.is_set():
                    self.ui_events.put(("status", self.tr("disconnected", error=exc)))
                    self.reconnect_event.wait(5)


