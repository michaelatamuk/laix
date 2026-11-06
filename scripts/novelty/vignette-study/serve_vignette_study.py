"""Serve the offline user-study app from data/vignette-study/v1."""

from __future__ import annotations

import functools
import http.server
import socketserver
import threading
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DIRECTORY = ROOT / "data" / "vignette-study" / "v1"


class _Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        print(f"{self.address_string()} {format % args}")


def main() -> int:
    handler = functools.partial(_Handler, directory=str(DIRECTORY))
    with socketserver.TCPServer(("127.0.0.1", 0), handler) as server:
        port = server.server_address[1]
        url = f"http://127.0.0.1:{port}/app/"
        print(f"Serving {DIRECTORY}")
        print(f"Open {url}")
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nStopped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
