from __future__ import annotations


def normalize_hex_color(value: str, fallback: str) -> str:
    text = str(value or "").strip()
    if not text.startswith("#"):
        text = f"#{text}"
    if len(text) == 4 and all(character in "0123456789abcdefABCDEF" for character in text[1:]):
        text = "#" + "".join(character * 2 for character in text[1:])
    if len(text) == 7 and all(character in "0123456789abcdefABCDEF" for character in text[1:]):
        return text.lower()
    return fallback


def hex_to_rgb(color: str) -> tuple[int, int, int]:
    normalized = normalize_hex_color(color, "#ffffff").lstrip("#")
    return int(normalized[0:2], 16), int(normalized[2:4], 16), int(normalized[4:6], 16)


def css_string(value: str) -> str:
    text = str(value or "").replace("\\", "\\\\").replace('"', '\\"').strip()
    return f'"{text}"' if text else '"Microsoft JhengHei"'


def normalize_aspect_ratio(value: str, fallback: str = "1:1") -> str:
    text = str(value or "").strip().lower().replace("：", ":").replace("/", ":")
    if not text:
        return fallback
    try:
        width, height = parse_aspect_ratio(text)
    except ValueError:
        return fallback
    return f"{width:g}:{height:g}"


def parse_aspect_ratio(value: str) -> tuple[float, float]:
    text = str(value or "").strip().lower().replace("：", ":").replace("/", ":")
    if ":" in text:
        left, right = text.split(":", 1)
        width = float(left.strip())
        height = float(right.strip())
    else:
        width = float(text)
        height = 1.0
    if width <= 0 or height <= 0:
        raise ValueError("Aspect ratio must be positive")
    return width, height


def normalize_blacklist_name(value: str) -> str:
    return str(value or "").strip().lstrip("@").casefold()
