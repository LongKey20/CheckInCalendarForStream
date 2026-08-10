from __future__ import annotations

import json
import mimetypes
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .constants import (
    AVATAR_CACHE_DIR,
    AVATAR_CACHE_META_FILE,
    AVATAR_CACHE_REQUEST_TIMEOUT_SECONDS,
    AVATAR_CACHE_TTL_SECONDS,
    LEGACY_AVATAR_CACHE_META_FILE,
    TWITCH_AVATAR_CACHE_DIR,
)


_USERNAME_RE = re.compile(r"[^a-z0-9_]+")


@dataclass
class AvatarResource:
    body: bytes
    content_type: str


class AvatarCache:
    def __init__(self, cache_days_getter=None) -> None:
        TWITCH_AVATAR_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        self.cache_days_getter = cache_days_getter
        self.metadata = self._load_metadata()
        self.transient: dict[str, AvatarResource] = {}

    @staticmethod
    def normalize_username(username: str) -> str:
        normalized = _USERNAME_RE.sub("", str(username or "").strip().lstrip("@").casefold())
        return normalized[:64]

    def avatar_url(self, username: str) -> str:
        normalized = self.normalize_username(username)
        return f"/avatar/{normalized}" if normalized else ""

    def unavatar_url(self, username: str) -> str:
        normalized = self.normalize_username(username)
        return f"https://unavatar.io/twitch/{normalized}" if normalized else ""

    def prepare(self, username: str) -> str:
        normalized = self.normalize_username(username)
        if not normalized:
            return ""
        if self._cache_ttl_seconds() > 0 and self._cached_file_is_valid(normalized):
            return self.avatar_url(normalized)
        self._fetch_latest(normalized)
        if self.resource(normalized):
            return self.avatar_url(normalized)
        return self.unavatar_url(normalized)

    def resource(self, username: str) -> AvatarResource | None:
        normalized = self.normalize_username(username)
        if not normalized:
            return None
        transient = self.transient.get(normalized)
        if transient:
            return transient
        entry = self.metadata.get(normalized, {})
        path = TWITCH_AVATAR_CACHE_DIR / str(entry.get("file", ""))
        if not path.is_file():
            path = AVATAR_CACHE_DIR / str(entry.get("file", ""))
        if not path.is_file():
            return None
        content_type = str(entry.get("content_type") or mimetypes.guess_type(path.name)[0] or "image/png")
        try:
            return AvatarResource(path.read_bytes(), content_type)
        except OSError:
            return None

    def _load_metadata(self) -> dict[str, dict]:
        source = AVATAR_CACHE_META_FILE if AVATAR_CACHE_META_FILE.exists() else LEGACY_AVATAR_CACHE_META_FILE
        try:
            data = json.loads(source.read_text(encoding="utf-8"))
        except (FileNotFoundError, OSError, json.JSONDecodeError):
            return {}
        if not isinstance(data, dict):
            return {}
        return {self.normalize_username(key): value for key, value in data.items() if isinstance(value, dict)}

    def _save_metadata(self) -> None:
        TWITCH_AVATAR_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        temp = AVATAR_CACHE_META_FILE.with_suffix(".tmp")
        temp.write_text(json.dumps(self.metadata, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(temp, AVATAR_CACHE_META_FILE)

    def _cache_ttl_seconds(self) -> int:
        if self.cache_days_getter is None:
            return AVATAR_CACHE_TTL_SECONDS
        try:
            days = int(self.cache_days_getter())
        except (TypeError, ValueError):
            days = 28
        return max(0, days) * 24 * 60 * 60

    def _cached_file_is_valid(self, username: str) -> bool:
        entry = self.metadata.get(username)
        if not entry:
            return False
        path = TWITCH_AVATAR_CACHE_DIR / str(entry.get("file", ""))
        if not path.is_file():
            path = AVATAR_CACHE_DIR / str(entry.get("file", ""))
        fetched_at = float(entry.get("fetched_at", 0) or 0)
        return path.is_file() and fetched_at > 0 and time.time() - fetched_at < self._cache_ttl_seconds()

    def _fetch_latest(self, username: str) -> None:
        url = f"https://unavatar.io/twitch/{username}?ttl=28d"
        request = Request(url, headers={"User-Agent": "StreamerTool/2.1"})
        try:
            with urlopen(request, timeout=AVATAR_CACHE_REQUEST_TIMEOUT_SECONDS) as response:
                status = int(getattr(response, "status", 200) or 200)
                headers = response.headers
                body = response.read()
        except HTTPError as error:
            status = int(error.code or 0)
            headers = error.headers
            try:
                body = error.read()
            except OSError:
                body = b""
        except (OSError, URLError, TimeoutError):
            return

        content_type = str(headers.get("content-type", "") or "").split(";", 1)[0].strip().lower()
        if not body or not content_type.startswith("image/"):
            return

        if (
            self._cache_ttl_seconds() <= 0
            or status == 429
            or str(headers.get("x-rate-limit-remaining", "")).strip() == "0"
        ):
            self.transient[username] = AvatarResource(body, content_type)
            return

        extension = mimetypes.guess_extension(content_type) or ".img"
        if extension == ".jpe":
            extension = ".jpg"
        filename = f"{username}{extension}"
        TWITCH_AVATAR_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        path = TWITCH_AVATAR_CACHE_DIR / filename
        temp = path.with_suffix(path.suffix + ".tmp")
        try:
            temp.write_bytes(body)
            os.replace(temp, path)
        except OSError:
            return
        self.metadata[username] = {
            "file": filename,
            "content_type": content_type,
            "fetched_at": time.time(),
            "rate_limit_limit": str(headers.get("x-rate-limit-limit", "")),
            "rate_limit_remaining": str(headers.get("x-rate-limit-remaining", "")),
            "rate_limit_reset": str(headers.get("x-rate-limit-reset", "")),
            "cache_status": str(headers.get("x-cache-status", "")),
        }
        self.transient.pop(username, None)
        self._save_metadata()
