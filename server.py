import http.server
import json
import os
import sys
from urllib.parse import urlparse
from pathlib import Path

if getattr(sys, "frozen", False):
    ROOT_DIR = Path(sys.executable).resolve().parent
    BUNDLE_DIR = Path(getattr(sys, "_MEIPASS", ROOT_DIR))
else:
    ROOT_DIR = Path(__file__).resolve().parent
    BUNDLE_DIR = ROOT_DIR

CONFIG_PATH = ROOT_DIR / "config" / "server_config.json"
CLIENT_CONFIG_PATH = ROOT_DIR / "config" / "client_config.json"
COMMAND_CONFIG_PATH = ROOT_DIR / "config" / "command.json"
HTML_PATH = BUNDLE_DIR / "TwitchCanlendar.html"
CONFIG_VERSION = "0.0.3"
DEFAULT_CONFIG = {
    "configVersion": CONFIG_VERSION,
    "host": "127.0.0.1",
    "port": 8000,
    "csvFolderPath": "csv",
    "csvPrefix": ""
}
DEFAULT_CLIENT_CONFIG = {
    "configVersion": CONFIG_VERSION,
    "channel": "",
    "displaySeconds": 6,
    "timeZone": "Asia/Tokyo",
    "dataUrl": "/calendar",
    "apiWriteUrl": "/api/write-csv",
    "style": "theme/default.css"
}
DEFAULT_COMMAND_CONFIG = {
    "configVersion": CONFIG_VERSION,
    "ShowCalendarCommand": [
        "!\u6708\u66c6"
    ]
}


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def read_json(path):
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return None

    return data if isinstance(data, dict) else None


def parse_config_version(value):
    text = str(value or "0.0.0").strip()
    parts = text.split(".")
    numbers = []

    for part in parts[:3]:
        try:
            numbers.append(int(part))
        except ValueError:
            numbers.append(0)

    while len(numbers) < 3:
        numbers.append(0)

    return tuple(numbers)


def is_version_less_than(current, target):
    return parse_config_version(current) < parse_config_version(target)


def run_version_migrations(data, migrations, previous_version):
    changed = False

    for target_version, migrate in migrations:
        if is_version_less_than(previous_version, target_version):
            changed = migrate(data) or changed

    return changed


def migrate_server_config(data, previous_version):
    return run_version_migrations(data, [
        # Add future server_config migrations here.
        # Example:
        # ("0.0.4", migrate_server_config_to_004),
    ], previous_version)


def migrate_client_config(data, previous_version):
    changed = run_version_migrations(data, [
        # Add future client_config migrations here.
        # Example:
        # ("0.0.4", migrate_client_config_to_004),
    ], previous_version)

    if "timeZoneHelp" in data:
        del data["timeZoneHelp"]
        changed = True

    return changed


def migrate_command_config(data, previous_version):
    return run_version_migrations(data, [
        # Add future command.json migrations here.
        # Example:
        # ("0.0.4", migrate_command_config_to_004),
    ], previous_version)


def merge_config_file(path, defaults, on_create=None, migrate=None):
    if not path.exists():
        data = defaults.copy()
        if on_create:
            on_create(data)
        write_json(path, data)
        return data

    data = read_json(path)
    if data is None:
        print(f"Warning: {path} could not be read as a JSON object. Using defaults in memory.")
        return defaults.copy()

    changed = False
    previous_version = data.get("configVersion", "0.0.0")

    if migrate and migrate(data, previous_version):
        changed = True

    for key, value in defaults.items():
        if key not in data:
            data[key] = value
            changed = True

    if data.get("configVersion") != CONFIG_VERSION:
        data["configVersion"] = CONFIG_VERSION
        changed = True

    if changed:
        write_json(path, data)

    return data


def prompt_for_twitch_channel():
    message = (
        "Please enter your Twitch channel name.\n"
        "This is the part of the URL after https://www.twitch.tv/{channel}, "
        "for example: https://www.twitch.tv/longkey -> longkey\n"
        "Twitch channel name: "
    )

    while True:
        try:
            channel = input(message).strip()
        except EOFError:
            return ""

        if channel:
            return channel

        print("Channel name is required. Please enter the Twitch channel name.")


def ensure_config_files():
    merge_config_file(
        CONFIG_PATH,
        DEFAULT_CONFIG,
        migrate=migrate_server_config
    )
    merge_config_file(
        CLIENT_CONFIG_PATH,
        DEFAULT_CLIENT_CONFIG,
        on_create=lambda data: data.update({"channel": prompt_for_twitch_channel()}),
        migrate=migrate_client_config
    )
    merge_config_file(
        COMMAND_CONFIG_PATH,
        DEFAULT_COMMAND_CONFIG,
        migrate=migrate_command_config
    )


def is_blank(value):
    return str(value or "").strip() == ""


def require_value(errors, config_name, data, key, help_text):
    if is_blank(data.get(key)):
        errors.append(f"{config_name}: '{key}' is required. {help_text}")


def require_warning(warnings, config_name, data, key, help_text):
    if is_blank(data.get(key)):
        warnings.append(f"{config_name}: '{key}' is empty. {help_text}")


def validate_config_files():
    errors = []
    warnings = []

    server_config = read_json(CONFIG_PATH)
    client_config = read_json(CLIENT_CONFIG_PATH)
    command_config = read_json(COMMAND_CONFIG_PATH)

    if server_config is None:
        errors.append("config/server_config.json must be a valid JSON object.")
    else:
        require_value(errors, "config/server_config.json", server_config, "host", "Example: 127.0.0.1")
        require_value(errors, "config/server_config.json", server_config, "csvFolderPath", "Example: csv")

        try:
            port = int(server_config.get("port"))
            if not 1 <= port <= 65535:
                raise ValueError
        except (TypeError, ValueError):
            errors.append("config/server_config.json: 'port' must be a number from 1 to 65535. Example: 8000")

    if client_config is None:
        errors.append("config/client_config.json must be a valid JSON object.")
    else:
        require_warning(
            warnings,
            "config/client_config.json",
            client_config,
            "channel",
            "Enter your Twitch channel name. It is the part after https://www.twitch.tv/{channel}."
        )
        require_value(
            errors,
            "config/client_config.json",
            client_config,
            "timeZone",
            "Enter an IANA time zone name. Examples: Asia/Tokyo, Asia/Taipei, America/New_York."
        )
        require_value(errors, "config/client_config.json", client_config, "dataUrl", "Example: /calendar")
        require_value(errors, "config/client_config.json", client_config, "apiWriteUrl", "Example: /api/write-csv")

        try:
            display_seconds = float(client_config.get("displaySeconds"))
            if display_seconds <= 0:
                raise ValueError
        except (TypeError, ValueError):
            errors.append("config/client_config.json: 'displaySeconds' must be a positive number. Example: 6")

    if command_config is None:
        errors.append("config/command.json must be a valid JSON object.")
    elif not isinstance(command_config.get("ShowCalendarCommand"), list):
        errors.append("config/command.json: 'ShowCalendarCommand' must be an array. Example: [\"!月曆\"]")

    if errors or warnings:
        stop_with_config_messages(errors, warnings)


def stop_with_config_messages(errors, warnings):
    red = "\033[31m"
    reset = "\033[0m"

    print(red)
    print("Config warning/error. The server was not started.")
    print("Please fix the following config values and start TwitchCanlendar again:")
    print()

    for warning in warnings:
        print(f"- Warning: {warning}")

    for error in errors:
        print(f"- Error: {error}")

    print(reset)
    wait_for_key("Press any key to close this window...")
    sys.exit(1)


def wait_for_key(message):
    print(message, end="", flush=True)

    if not sys.stdin.isatty():
        print()
        return

    if os.name == "nt":
        try:
            import msvcrt
            msvcrt.getch()
            print()
            return
        except Exception:
            pass

    try:
        input()
    except EOFError:
        print()


def load_config():
    ensure_config_files()
    validate_config_files()

    if not CONFIG_PATH.exists():
        return DEFAULT_CONFIG.copy()

    try:
        with CONFIG_PATH.open("r", encoding="utf-8") as f:
            config = json.load(f)
    except Exception:
        return DEFAULT_CONFIG.copy()

    return {
        "host": str(config.get("host", DEFAULT_CONFIG["host"])),
        "port": int(config.get("port", DEFAULT_CONFIG["port"])),
        "csvFolderPath": str(config.get("csvFolderPath", DEFAULT_CONFIG["csvFolderPath"])),
        "csvPrefix": str(config.get("csvPrefix", DEFAULT_CONFIG["csvPrefix"]))
    }


def resolve_csv_folder(value):
    path = Path(value)
    if path.is_absolute():
        return path
    return ROOT_DIR / path


def get_csv_filename(date=None):
    from datetime import date as dt_date
    current = date or dt_date.today()
    return f"{CSV_PREFIX}{current.year}-{current.month:02d}.csv"


def get_csv_file(date=None):
    return CSV_FOLDER / get_csv_filename(date)


SERVER_CONFIG = load_config()
CSV_FOLDER = resolve_csv_folder(SERVER_CONFIG["csvFolderPath"])
CSV_PREFIX = SERVER_CONFIG["csvPrefix"]
CSV_FOLDER.mkdir(parents=True, exist_ok=True)


class RequestHandler(http.server.SimpleHTTPRequestHandler):
    def send_html(self):
        try:
            data = HTML_PATH.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        except Exception as e:
            self.send_error(500, str(e))

    def do_GET(self):
        request_path = urlparse(self.path).path

        if request_path in ("/", "/TwitchCanlendar.html"):
            return self.send_html()

        if request_path == "/calendar":
            target_path = get_csv_file()
            if not target_path.exists():
                self.send_error(404, "CSV file not found")
                return

            try:
                data = target_path.read_text(encoding="utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/csv; charset=utf-8")
                self.send_header("Content-Length", str(len(data.encode("utf-8"))))
                self.end_headers()
                self.wfile.write(data.encode("utf-8"))
            except Exception as e:
                self.send_error(500, str(e))
            return

        return super().do_GET()

    def do_POST(self):
        if self.path != "/api/write-csv":
            self.send_error(404, "Not Found")
            return

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        try:
            payload = json.loads(body.decode("utf-8"))
            csv_text = payload.get("csv")
            target_path = get_csv_file()

            if not isinstance(csv_text, str):
                raise ValueError("Missing csv content")

            # Normalize newlines and remove empty lines before writing.
            normalized = csv_text.replace("\r\n", "\n").replace("\r", "\n")
            lines = [line for line in normalized.split("\n") if line.strip() != ""]
            cleaned_text = "\r\n".join(lines)

            target_path.write_bytes(cleaned_text.encode("utf-8"))
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"success": True}).encode("utf-8"))
        except Exception as e:
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))

    def log_message(self, format, *args):
        return

if __name__ == "__main__":
    os.chdir(ROOT_DIR)
    server_address = (SERVER_CONFIG["host"], SERVER_CONFIG["port"])
    httpd = http.server.ThreadingHTTPServer(server_address, RequestHandler)
    print(f"Serving HTTP on http://{server_address[0]}:{server_address[1]}")
    print(f"CSV folder: {CSV_FOLDER}")
    print(f"Current CSV file: {get_csv_file()}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("Shutting down server")
        httpd.server_close()
