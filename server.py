import http.server
import json
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
HTML_PATH = BUNDLE_DIR / "TwitchCanlendar.html"
DEFAULT_CONFIG = {
    "host": "127.0.0.1",
    "port": 8000,
    "csvFolderPath": "csv",
    "csvPrefix": ""
}


def load_config():
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
    import os
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
