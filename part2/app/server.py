
"""HTTP API for the lab queue."""

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from app.queue import join, take


def serve(host: str, port: int, data_dir: str) -> None:
    """Listen until the process is stopped. Use join and take from app.queue."""

    queue_path = Path(data_dir) / "queue.txt"
    queue_path.parent.mkdir(parents=True, exist_ok=True)

    class QueueHandler(BaseHTTPRequestHandler):

        def send_text(self, status: int, body: str) -> None:
            payload = body.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def do_GET(self) -> None:
            if self.path == "/health":
                self.send_text(200, "ok")
            else:
                self.send_text(404, "not found")

        def do_POST(self) -> None:
            if self.path == "/join":
                try:
                    length = int(self.headers.get("Content-Length", "0"))
                    body = self.rfile.read(length).decode("utf-8")
                    data = json.loads(body)

                    if not isinstance(data, dict):
                        raise TypeError("Invalid JSON object")

                    name = data.get("name")
                    if not isinstance(name, str):
                        raise TypeError("Invalid name")

                    ticket = join(queue_path, name)
                    self.send_text(200, str(ticket))

                except (ValueError, TypeError, UnicodeDecodeError, json.JSONDecodeError):
                    self.send_text(400, "invalid name")

            elif self.path == "/next":
                try:
                    name = take(queue_path)
                    self.send_text(200, name)
                except LookupError:
                    self.send_text(404, "empty")

            else:
                self.send_text(404, "not found")

        def log_message(self, format: str, *args: object) -> None:
            print(f"{self.address_string()} - {format % args}")

    server = ThreadingHTTPServer((host, port), QueueHandler)
    print(f"Queue server listening on {host}:{port}")
    server.serve_forever()


def main() -> None:
    port = int(os.environ.get("PORT", "8000"))
    data_dir = os.environ.get("DATA_DIR", "/data")
    serve("0.0.0.0", port, data_dir)


if __name__ == "__main__":
    main()
