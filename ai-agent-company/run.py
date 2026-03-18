#!/usr/bin/env python3
"""
GestorIA — entry point.
Starts FastAPI (webhooks + REST API) on port 8000
and Gradio dashboard on port 7861 concurrently.

Usage:
  python run.py              # both services (development)
  python run.py api          # FastAPI only
  python run.py dashboard    # Gradio only
  python run.py --prod       # rejected — use Gunicorn via Docker/compose
"""
import sys
import os
import logging
import threading
import uvicorn

sys.path.insert(0, os.path.dirname(__file__))

# Configure root logger before importing any src modules so every module
# picks up the same level and format (container-friendly: no file handler).
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)


def run_api():
    uvicorn.run(
        "src.api:app",
        host="0.0.0.0",
        port=8000,
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
        reload=False,
    )


def run_dashboard():
    from src.app import build_app
    demo = build_app()

    # Gradio 6+ note: theme= and css= live in gr.Blocks() (src/app.py build_app).
    # If a future Gradio release moves them to .launch(), the migration pattern is:
    #
    #   import gradio as gr
    #   demo.launch(
    #       theme=gr.themes.Soft(primary_hue="indigo"),
    #       css=".gradio-container { max-width: 1100px !important; }",
    #       server_name="0.0.0.0",
    #       server_port=7861,
    #       show_error=True,
    #       share=False,
    #   )
    #
    demo.launch(
        server_name="0.0.0.0",
        server_port=7861,
        show_error=True,
        share=False,   # never expose a public Gradio tunnel in production
        quiet=False,
    )


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"

    if mode in ("--prod", "--production", "prod", "production"):
        print(
            "⚠️  GestorIA — modo producción\n"
            "   run.py no debe usarse en producción.\n"
            "   Usa Gunicorn a través de Docker / docker compose:\n\n"
            "     docker compose up -d\n\n"
            "   o directamente:\n"
            "     gunicorn -k uvicorn.workers.UvicornWorker \\\n"
            "              --workers 4 --bind 0.0.0.0:8000 src.api:app\n"
        )
        sys.exit(1)

    if mode == "api":
        run_api()
    elif mode == "dashboard":
        run_dashboard()
    else:
        # Default: run both concurrently (development / single-container compose)
        api_thread = threading.Thread(target=run_api, daemon=True)
        api_thread.start()
        print("✅ FastAPI arrancando en http://0.0.0.0:8000")
        print("✅ Gradio dashboard arrancando en http://0.0.0.0:7861")
        run_dashboard()  # blocks in main thread
