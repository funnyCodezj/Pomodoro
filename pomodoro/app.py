"""Pomodoro Timer Desktop App - Entry Point

Starts the FastAPI backend server and opens a PyWebView window.
"""

import threading
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

import webview
import uvicorn

from backend.main import app as fastapi_app

PORT = 8765


def start_server():
    uvicorn.run(fastapi_app, host="127.0.0.1", port=PORT, log_level="warning")


def main():
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    webview.create_window(
        "🍅 番茄钟",
        f"http://127.0.0.1:{PORT}",
        width=420,
        height=700,
        resizable=False,
        frameless=False,
        text_select=True,
    )
    webview.start()


if __name__ == "__main__":
    main()
