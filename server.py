# -*- coding: utf-8 -*-
import http.server
import json
import os
import sys
import tempfile
import urllib.error
import urllib.request
import zipfile
from datetime import datetime, timezone
from urllib.parse import urlparse, parse_qs
from pathlib import Path

# Ensure UTF-8 encoding for file operations on Windows
if sys.platform == "win32":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")

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
MANIFEST_PATH = ROOT_DIR / "manifest.json"
BUNDLED_MANIFEST_PATH = BUNDLE_DIR / "manifest.json"
ASSETS_STAMP_PATH = ROOT_DIR / ".assets-installed.json"
CONFIG_VERSION = "0.0.3"
DOWNLOAD_USER_AGENT = "TwitchCanlendar"
GITHUB_API_ACCEPT = "application/vnd.github+json"
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


def resolve_manifest_path():
    if MANIFEST_PATH.exists():
        return MANIFEST_PATH
    if BUNDLED_MANIFEST_PATH.exists():
        return BUNDLED_MANIFEST_PATH
    return None


def load_manifest():
    manifest_path = resolve_manifest_path()
    if manifest_path is None:
        return None

    data = read_json(manifest_path)
    if not isinstance(data, dict):
        print(f"Warning: {manifest_path} is not a valid JSON object. Skipping asset download.")
        return None

    return data


def normalize_release_tag(value):
    text = str(value or "").strip()
    if not text:
        return f"v{CONFIG_VERSION}"
    # If the tag already starts with "v" or is a custom format like "Version-X.X.X-Release",
    # return it as-is instead of adding "v" prefix
    if text.startswith("v") or text.startswith("Version"):
        return text
    return f"v{text}"


def resolve_repository(manifest):
    repository = str(manifest.get("repository") or "").strip().strip("/")
    if not repository:
        raise ValueError("manifest.json must define 'repository'.")
    return repository


def resolve_release_tag(manifest):
    return normalize_release_tag(manifest.get("releaseTag") or CONFIG_VERSION)


def resolve_asset_name(manifest, release_tag):
    asset_name = str(manifest.get("assetName") or "").strip()
    if asset_name:
        return asset_name
    version = release_tag.lstrip("v")
    return f"TwitchCanlendar-assets-{version}.zip"


def normalize_required_files(manifest):
    required_files = manifest.get("requiredFiles")
    if required_files is None:
        required_files = manifest.get("files", [])

    if not isinstance(required_files, list):
        raise ValueError("manifest.json 'requiredFiles' must be an array.")

    paths = []
    for entry in required_files:
        if isinstance(entry, str):
            relative_path = entry.strip()
            optional = False
        elif isinstance(entry, dict):
            relative_path = str(entry.get("path") or "").strip()
            optional = bool(entry.get("optional"))
        else:
            raise ValueError("Each requiredFiles entry must be a string or object.")

        if not relative_path:
            raise ValueError("requiredFiles contains an empty path.")
        if optional:
            continue
        paths.append(relative_path)

    if not paths:
        raise ValueError("manifest.json must list at least one required file.")

    return paths


def required_files_present(required_files):
    for relative_path in required_files:
        destination = ROOT_DIR / relative_path
        if not destination.exists() or destination.stat().st_size <= 0:
            return False
    return True


def read_assets_stamp():
    data = read_json(ASSETS_STAMP_PATH)
    return data if isinstance(data, dict) else None


def write_assets_stamp(release_tag, asset_name, download_url):
    write_json(ASSETS_STAMP_PATH, {
        "releaseTag": release_tag,
        "assetName": asset_name,
        "downloadUrl": download_url,
        "appVersion": CONFIG_VERSION,
        "installedAt": datetime.now(timezone.utc).isoformat()
    })


def assets_install_is_current(manifest, release_tag, asset_name, required_files):
    if not required_files_present(required_files):
        return False

    stamp = read_assets_stamp()
    if stamp is None:
        # If stamp file doesn't exist but all required files are present,
        # assume assets are current to avoid unnecessary downloads
        return True

    return (
        stamp.get("releaseTag") == release_tag and
        stamp.get("assetName") == asset_name and
        stamp.get("appVersion") == CONFIG_VERSION
    )


def github_api_request(url):
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": DOWNLOAD_USER_AGENT,
            "Accept": GITHUB_API_ACCEPT
        }
    )

    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_release_asset_url(repository, release_tag, asset_name):
    api_url = f"https://api.github.com/repos/{repository}/releases/tags/{release_tag}"
    release = github_api_request(api_url)

    assets = release.get("assets")
    if not isinstance(assets, list):
        raise ValueError(f"Release '{release_tag}' has no downloadable assets.")

    for asset in assets:
        if asset.get("name") == asset_name:
            download_url = asset.get("browser_download_url")
            if download_url:
                return download_url
            break

    available = ", ".join(
        str(item.get("name"))
        for item in assets
        if isinstance(item, dict) and item.get("name")
    )
    hint = f" Available assets: {available}" if available else ""
    raise ValueError(
        f"Asset '{asset_name}' was not found in GitHub release '{release_tag}'.{hint}"
    )


def download_bytes(url):
    request = urllib.request.Request(url, headers={"User-Agent": DOWNLOAD_USER_AGENT})

    with urllib.request.urlopen(request, timeout=120) as response:
        data = response.read()

    if not data:
        raise ValueError("Downloaded file is empty.")

    return data


def safe_extract_zip(zip_path, destination_dir):
    destination_dir = destination_dir.resolve()

    with zipfile.ZipFile(zip_path) as archive:
        for member in archive.namelist():
            if member.endswith("/"):
                continue

            target_path = (destination_dir / member).resolve()
            if not str(target_path).startswith(str(destination_dir)):
                raise ValueError(f"Unsafe path in asset zip: {member}")

        archive.extractall(destination_dir)


def install_assets_from_release(manifest):
    manifest_version = str(manifest.get("manifestVersion") or "").strip()
    if manifest_version != "2":
        raise ValueError(
            "Unsupported manifest.json version. Expected manifestVersion \"2\" for GitHub Release assets."
        )

    repository = resolve_repository(manifest)
    release_tag = resolve_release_tag(manifest)
    asset_name = resolve_asset_name(manifest, release_tag)
    required_files = normalize_required_files(manifest)

    if assets_install_is_current(manifest, release_tag, asset_name, required_files):
        print(f"Assets already installed for {release_tag} ({asset_name}).")
        return

    download_url = fetch_release_asset_url(repository, release_tag, asset_name)
    print(f"Downloading assets from GitHub Release {release_tag}...")
    print(f"  {download_url}")

    payload = download_bytes(download_url)

    with tempfile.TemporaryDirectory() as temp_dir:
        zip_path = Path(temp_dir) / asset_name
        zip_path.write_bytes(payload)
        safe_extract_zip(zip_path, ROOT_DIR)

    missing_files = [
        relative_path
        for relative_path in required_files
        if not (ROOT_DIR / relative_path).exists()
    ]
    if missing_files:
        raise ValueError(
            "Asset zip was extracted, but required files are still missing: "
            + ", ".join(missing_files)
        )

    write_assets_stamp(release_tag, asset_name, download_url)
    print("Installed assets:")
    for relative_path in required_files:
        print(f"  - {relative_path}")


def stop_with_asset_errors(errors):
    red = "\033[31m"
    reset = "\033[0m"
    print(red)
    print("Required assets could not be installed. The server was not started.")
    for error in errors:
        print(f"- {error}")
    print()
    print("Publish a GitHub Release with the matching asset zip, for example:")
    print("  gh release create v0.0.3 dist/TwitchCanlendar.exe dist/CheckInCalendar-assets-0.0.3.zip")
    print(reset)
    wait_for_key("Press any key to close this window...")
    sys.exit(1)


def ensure_assets_from_manifest():
    manifest = load_manifest()
    if manifest is None:
        stop_with_asset_errors(["manifest.json not found. Please ensure manifest.json exists in the application directory."])

    try:
        install_assets_from_release(manifest)
    except Exception as exc:
        stop_with_asset_errors([str(exc)])


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


def initialize_csv_file_if_needed(csv_path):
    """Create CSV file with headers if it doesn't exist."""
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    
    if not csv_path.exists() or csv_path.stat().st_size <= 0:
        # CSV headers matching the frontend schema
        headers = "date,username,displayName,timestamp,isFirst"
        csv_path.write_text(headers, encoding="utf-8")
        print(f"Initialized CSV file: {csv_path}")


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


SERVER_CONFIG = None
CSV_FOLDER = None
CSV_PREFIX = ""


def parse_csv_rows(csv_text):
    """Parse CSV text into rows, handling quoted fields."""
    rows = []
    current = []
    field = ""
    in_quotes = False

    for ch in csv_text:
        if ch == '"':
            if in_quotes and field and field[-1:] != '"':
                in_quotes = False
            else:
                in_quotes = True
            field += ch
        elif ch == ',' and not in_quotes:
            current.append(field)
            field = ""
        elif ch == '\n' and not in_quotes:
            if field or current:
                current.append(field)
                rows.append(current)
                current = []
                field = ""
        else:
            field += ch

    if current or field:
        current.append(field)
        if current:
            rows.append(current)

    return rows


def group_csv_rows_by_month(rows):
    """Group CSV rows by year-month based on date column (first column)."""
    from collections import defaultdict
    
    month_groups = defaultdict(list)
    headers = None
    
    for i, row in enumerate(rows):
        if i == 0:
            # Headers row
            headers = row
            continue
        
        if not row or not row[0].strip():
            continue
        
        # Extract date from first column (format: YYYY-MM-DD)
        date_str = row[0].strip()
        if '-' not in date_str or len(date_str) < 7:
            continue
        
        try:
            year_month = date_str[:7]  # YYYY-MM
            month_groups[year_month].append(row)
        except (IndexError, ValueError):
            continue
    
    return headers, month_groups


def merge_csv_with_file(file_path, new_rows):
    """Merge new rows with existing CSV file, avoiding duplicates."""
    # Read existing rows
    existing_rows = []
    if file_path.exists():
        try:
            existing_text = file_path.read_text(encoding="utf-8")
            existing_rows = parse_csv_rows(existing_text)
            if existing_rows:
                existing_rows = existing_rows[1:]  # Skip header
        except Exception:
            pass
    
    # Create a set of existing (date, username) pairs to detect duplicates
    existing_keys = set()
    for row in existing_rows:
        if len(row) >= 2:
            # Key is (date, username)
            key = (row[0].strip(), row[1].strip())
            existing_keys.add(key)
    
    # Add only new rows
    merged_rows = list(existing_rows)
    for new_row in new_rows:
        if len(new_row) >= 2:
            key = (new_row[0].strip(), new_row[1].strip())
            if key not in existing_keys:
                merged_rows.append(new_row)
    
    return merged_rows


def save_csv_rows_to_files(headers, month_groups, csv_folder, csv_prefix):
    """Save grouped CSV rows to corresponding month files."""
    if not headers:
        return
    
    header_text = ",".join(headers)
    
    for year_month, rows in month_groups.items():
        file_name = f"{csv_prefix}{year_month}.csv"
        file_path = csv_folder / file_name
        
        # Merge with existing file
        all_rows = merge_csv_with_file(file_path, rows)
        
        # Format and write
        csv_folder.mkdir(parents=True, exist_ok=True)
        file_lines = [header_text]
        for row in all_rows:
            # Properly quote fields that contain commas, quotes, or newlines
            formatted_row = []
            for field in row:
                field_str = str(field or "")
                if "," in field_str or '"' in field_str or "\n" in field_str:
                    escaped = field_str.replace('"', '""')
                    field_str = f'"{escaped}"'
                formatted_row.append(field_str)
            file_lines.append(",".join(formatted_row))
        
        file_content = "\r\n".join(file_lines)
        file_path.write_text(file_content, encoding="utf-8")
        print(f"CSV saved: {file_path}")


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
            # Support optional query parameters for specific year/month
            # Examples: /calendar, /calendar?year=2026&month=6, /calendar?year=2026&month=06
            query_params = {}
            parsed_url = urlparse(self.path)
            if parsed_url.query:
                params = parse_qs(parsed_url.query)
                if 'year' in params and 'month' in params:
                    try:
                        year = int(params['year'][0])
                        month = int(params['month'][0])
                        if 1 <= month <= 12 and 2000 <= year <= 2099:
                            query_params['year'] = year
                            query_params['month'] = month
                    except (ValueError, IndexError):
                        pass
            
            # If query parameters are provided, use them; otherwise use current date
            if query_params:
                target_path = CSV_FOLDER / f"{CSV_PREFIX}{query_params['year']}-{query_params['month']:02d}.csv"
            else:
                target_path = get_csv_file()
            
            # If CSV file doesn't exist, return header-only CSV (empty sign-in records)
            if not target_path.exists():
                csv_header = "date,username,displayName,timestamp,isFirst"
                data = csv_header.encode("utf-8")
            else:
                try:
                    data = target_path.read_text(encoding="utf-8").encode("utf-8")
                except Exception as e:
                    self.send_error(500, str(e))
                    return

            self.send_response(200)
            self.send_header("Content-Type", "text/csv; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
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

            if not isinstance(csv_text, str):
                raise ValueError("Missing csv content")

            # Normalize newlines and remove empty lines
            normalized = csv_text.replace("\r\n", "\n").replace("\r", "\n")
            lines = [line for line in normalized.split("\n") if line.strip() != ""]
            cleaned_text = "\r\n".join(lines)
            
            # Parse CSV and group by month
            rows = parse_csv_rows(cleaned_text)
            if not rows or len(rows) < 2:
                raise ValueError("CSV must contain header and at least one data row")
            
            headers, month_groups = group_csv_rows_by_month(rows)
            if not headers:
                raise ValueError("Invalid CSV format: missing headers")
            
            # Save to appropriate month files
            save_csv_rows_to_files(headers, month_groups, CSV_FOLDER, CSV_PREFIX)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"success": True}).encode("utf-8"))
        except Exception as e:
            error_msg = str(e)
            print(f"CSV save error: {error_msg}")
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"success": False, "error": error_msg}).encode("utf-8"))

    def log_message(self, format, *args):
        # Log important messages (errors and POST requests)
        message = format % args
        if "POST" in message or "400" in message or "500" in message:
            print(f"[{self.log_date_time_string()}] {self.client_address[0]} - {message}")


def parse_csv_rows(csv_text):
    """Parse CSV text into rows, handling quoted fields."""
    rows = []
    current = []
    field = ""
    in_quotes = False

    for ch in csv_text:
        if ch == '"':
            if in_quotes and field and field[-1:] != '"':
                in_quotes = False
            else:
                in_quotes = True
            field += ch
        elif ch == ',' and not in_quotes:
            current.append(field)
            field = ""
        elif ch == '\n' and not in_quotes:
            if field or current:
                current.append(field)
                rows.append(current)
                current = []
                field = ""
        else:
            field += ch

    if current or field:
        current.append(field)
        if current:
            rows.append(current)

    return rows


def group_csv_rows_by_month(rows):
    """Group CSV rows by year-month based on date column (first column)."""
    from collections import defaultdict
    
    month_groups = defaultdict(list)
    headers = None
    
    for i, row in enumerate(rows):
        if i == 0:
            # Headers row
            headers = row
            continue
        
        if not row or not row[0].strip():
            continue
        
        # Extract date from first column (format: YYYY-MM-DD)
        date_str = row[0].strip()
        if '-' not in date_str or len(date_str) < 7:
            continue
        
        try:
            year_month = date_str[:7]  # YYYY-MM
            month_groups[year_month].append(row)
        except (IndexError, ValueError):
            continue
    
    return headers, month_groups


def merge_csv_with_file(file_path, new_rows):
    """Merge new rows with existing CSV file, avoiding duplicates."""
    # Read existing rows
    existing_rows = []
    if file_path.exists():
        try:
            existing_text = file_path.read_text(encoding="utf-8")
            existing_rows = parse_csv_rows(existing_text)
            if existing_rows:
                existing_rows = existing_rows[1:]  # Skip header
        except Exception:
            pass
    
    # Create a set of existing (date, username) pairs to detect duplicates
    existing_keys = set()
    for row in existing_rows:
        if len(row) >= 2:
            # Key is (date, username)
            key = (row[0].strip(), row[1].strip())
            existing_keys.add(key)
    
    # Add only new rows
    merged_rows = list(existing_rows)
    for new_row in new_rows:
        if len(new_row) >= 2:
            key = (new_row[0].strip(), new_row[1].strip())
            if key not in existing_keys:
                merged_rows.append(new_row)
    
    return merged_rows


if __name__ == "__main__":
    try:
        os.chdir(ROOT_DIR)
    except OSError:
        # If os.chdir fails (e.g., due to Chinese characters in path),
        # continue anyway as we use absolute paths via ROOT_DIR
        pass
    ensure_assets_from_manifest()
    SERVER_CONFIG = load_config()
    CSV_FOLDER = resolve_csv_folder(SERVER_CONFIG["csvFolderPath"])
    CSV_PREFIX = SERVER_CONFIG["csvPrefix"]
    CSV_FOLDER.mkdir(parents=True, exist_ok=True)
    
    # Initialize CSV file with headers if needed
    csv_file = get_csv_file()
    initialize_csv_file_if_needed(csv_file)

    server_address = (SERVER_CONFIG["host"], SERVER_CONFIG["port"])
    httpd = http.server.ThreadingHTTPServer(server_address, RequestHandler)
    print(f"Serving HTTP on http://{server_address[0]}:{server_address[1]}")
    print(f"CSV folder: {CSV_FOLDER}")
    print(f"Current CSV file: {csv_file}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("Shutting down server")
        httpd.server_close()
