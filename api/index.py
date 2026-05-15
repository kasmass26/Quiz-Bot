from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os

import requests  # type: ignore


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_local_env():
    if os.environ.get("VERCEL"):
        return

    env_path = os.path.join(BASE_DIR, ".env")

    try:
        with open(env_path, encoding="utf-8") as env_file:
            for line in env_file:
                line = line.strip()

                if not line or line.startswith("#") or "=" not in line:
                    continue

                key, value = line.split("=", 1)
                key = key.strip()

                if key.startswith("export "):
                    key = key[7:].strip()

                if key and key not in os.environ:
                    os.environ[key] = value.strip().strip("'\"")
    except FileNotFoundError:
        pass


load_local_env()
BOT_TOKEN = os.environ.get("BOT_TOKEN")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}" if BOT_TOKEN else None


class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()

        token_status = "configured" if BOT_TOKEN else "missing"
        self.wfile.write(
            f"Bot webhook is running. BOT_TOKEN is {token_status}.".encode("utf-8")
        )

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        try:
            update = json.loads(body)
            message = update.get("message") or update.get("edited_message")

            if message:
                chat_id = message.get("chat", {}).get("id")
                text = message.get("text") or ""
                command = text.strip().split(maxsplit=1)[0] if text.strip() else ""

                if chat_id and command.split("@", 1)[0] == "/start":
                    send_message(chat_id, "Yo! Bot is alive on Vercel")

        except json.JSONDecodeError as e:
            print("BAD_JSON:", str(e))
        except Exception as e:
            print("ERROR:", str(e))

        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK")


def send_message(chat_id, text):
    if not TELEGRAM_API_URL:
        print("BOT_TOKEN missing")
        return False

    url = f"{TELEGRAM_API_URL}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        return True
    except requests.RequestException as e:
        print("TELEGRAM_SEND_ERROR:", str(e))
        return False


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    server = HTTPServer(("", port), handler)
    print(f"Serving webhook locally on http://localhost:{port}")
    server.serve_forever()
