#!/usr/bin/env python3
"""
GestorIA — entry point.
Starts FastAPI (webhooks + REST API) on port 8000
and Gradio dashboard on port 7861 concurrently.
"""
import sys
import os
import threading
import uvicorn

sys.path.insert(0, os.path.dirname(__file__))


def run_api():
    uvicorn.run(
        "src.api:app",
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=False,
    )


def run_dashboard():
    from src.app import build_app
    demo = build_app()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7861,
        show_error=True,
        quiet=True,
    )


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"

    if mode == "api":
        run_api()
    elif mode == "dashboard":
        run_dashboard()
    else:
        # Default: run both
        api_thread = threading.Thread(target=run_api, daemon=True)
        api_thread.start()
        print("✅ FastAPI arrancando en http://0.0.0.0:8000")
        print("✅ Gradio dashboard arrancando en http://0.0.0.0:7861")
        run_dashboard()  # blocks in main thread
