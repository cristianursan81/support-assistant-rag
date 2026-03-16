"""
app.py  ·  v2.1  —  VERSIÓN LIMPIA Y DEFINITIVA
------------------------------------------------
Support Assistant RAG · Cristian Ursan
Tema: Negro y verde terminal (Matrix/CRT)
Features: Streaming, memoria de conversación, UI premium
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import gradio as gr
from src.rag import get_assistant

# ── Preguntas de ejemplo ────────────────────────────────────────────
EXAMPLE_QUESTIONS = [
    "¿Cuál es el proceso de escalado para clientes premium?",
    "¿Qué KPIs usas para medir la performance de un equipo de soporte?",
    "¿Cómo defines las prioridades de tickets según el SLA?",
    "¿Cómo haces el onboarding de un nuevo agente de soporte?",
    "¿Qué métricas de calidad usas en el QA de soporte?",
    "¿Cómo gestionas un equipo distribuido en múltiples zonas horarias?",
    "¿Cómo gestiono una crisis de nivel 1?",
    "¿Cuáles son las 10 automatizaciones más importantes en Zendesk?",
]

# ── CSS: Tema Matrix / Terminal CRT ────────────────────────────────
CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=VT323&family=Roboto+Mono:wght@300;400;500&display=swap');

:root {
    --bg-primary:    #1a1a1a;
    --bg-secondary:  #1f261f;
    --bg-card:       #222e22;
    --bg-msg:        #1c231c;
    --border:        #0a2a0a;
    --border-bright: #0f3f0f;
    --accent:        #00ff41;
    --accent-dim:    #00cc33;
    --accent-glow:   rgba(0, 255, 65, 0.15);
    --accent-dark:   rgba(0, 255, 65, 0.05);
    --green-bright:  #39ff14;
    --green-dim:     #007a1e;
    --green-muted:   #004410;
    --text-body:     #b8ffcc;
    --font-mono:     'Share Tech Mono', monospace;
    --font-display:  'VT323', monospace;
    --font-body:     'Roboto Mono', monospace;
}

* { box-sizing: border-box; }

/* Scanlines CRT */
body::before {
    content: '';
    position: fixed;
    top: 0; left: 0;
    width: 100%; height: 100%;
    background: repeating-linear-gradient(
        0deg,
        transparent,
        transparent 2px,
        rgba(0, 255, 65, 0.015) 2px,
        rgba(0, 255, 65, 0.015) 4px
    );
    pointer-events: none;
    z-index: 9999;
}

body, .gradio-container {
    background: var(--bg-primary) !important;
    font-family: var(--font-mono) !important;
    color: var(--accent) !important;
}

.gradio-container {
    max-width: 1100px !important;
    margin: 0 auto !important;
    padding: 0 !important;
}

/* ── HEADER ── */
.header-wrap {
    padding: 32px 40px 0;
    border-bottom: 1px solid var(--border-bright);
    position: relative;
}

.header-wrap::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--accent), transparent);
    animation: glowline 3s ease-in-out infinite;
}

@keyframes glowline {
    0%, 100% { opacity: 0.3; }
    50% { opacity: 1; }
}

.header-top {
    display: flex;
    align-items: center;
    gap: 16px;
    margin-bottom: 4px;
}

.status-dot {
    width: 10px; height: 10px;
    border-radius: 50%;
    background: var(--accent);
    box-shadow: 0 0 6px var(--accent), 0 0 12px var(--accent), 0 0 24px var(--accent);
    animation: blink 1.2s step-end infinite;
    flex-shrink: 0;
}

@keyframes blink {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.1; }
}

.header-title {
    font-family: var(--font-display) !important;
    font-size: 38px !important;
    font-weight: 400 !important;
    color: var(--accent) !important;
    letter-spacing: 4px !important;
    margin: 0 !important;
    line-height: 1 !important;
    text-shadow: 0 0 10px var(--accent), 0 0 30px var(--accent-dim);
}

.header-sub {
    font-size: 10px !important;
    color: var(--green-dim) !important;
    font-family: var(--font-mono) !important;
    letter-spacing: 3px;
    text-transform: uppercase;
    margin: 2px 0 16px !important;
    padding-left: 26px;
}

.header-meta {
    display: flex;
    gap: 28px;
    padding: 12px 0;
    border-top: 1px solid var(--border);
}

.meta-chip {
    font-size: 10px;
    font-family: var(--font-mono);
    color: var(--green-dim);
    text-transform: uppercase;
    letter-spacing: 1px;
}

.meta-chip::before { content: '> '; color: var(--accent-dim); }
.meta-chip span {
    color: var(--accent);
    text-shadow: 0 0 6px var(--accent);
}

/* ── MAIN ── */
.main-wrap { padding: 20px 40px 40px; }

/* ── CHATBOT ── */
.chatbot-wrap .label-wrap { display: none !important; }

.chatbot-wrap > div {
    background: var(--bg-secondary) !important;
    border: 1px solid var(--border-bright) !important;
    border-radius: 2px !important;
    box-shadow: 0 0 30px rgba(0,255,65,0.04), inset 0 0 60px rgba(0,0,0,0.6) !important;
}

/* Usuario */
.message.user, div[data-testid="user"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border-bright) !important;
    border-radius: 2px !important;
    color: var(--accent) !important;
    font-family: var(--font-mono) !important;
    font-size: 13px !important;
    line-height: 1.6 !important;
    padding: 12px 16px !important;
}

/* Asistente */
.message.bot, div[data-testid="bot"] {
    background: var(--bg-msg) !important;
    border: 1px solid var(--border) !important;
    border-left: 2px solid var(--accent) !important;
    border-radius: 0 2px 2px 0 !important;
    color: var(--text-body) !important;
    font-family: var(--font-body) !important;
    font-size: 13px !important;
    line-height: 1.85 !important;
    padding: 16px 20px !important;
}

/* Forzar colores internos del asistente */
div[data-testid="bot"],
div[data-testid="bot"] p,
div[data-testid="bot"] li,
div[data-testid="bot"] span,
div[data-testid="bot"] div,
div[data-testid="bot"] * {
    color: #b8ffcc !important;
}

div[data-testid="bot"] strong {
    color: var(--green-bright) !important;
    text-shadow: 0 0 6px var(--accent);
}

div[data-testid="bot"] code {
    background: #162016 !important;
    color: var(--accent) !important;
    font-family: var(--font-mono) !important;
    padding: 1px 6px !important;
    border: 1px solid var(--border-bright) !important;
    border-radius: 2px !important;
    font-size: 11px !important;
}

div[data-testid="bot"] ul,
div[data-testid="bot"] ol { padding-left: 20px !important; margin: 8px 0 !important; }
div[data-testid="bot"] li { margin-bottom: 6px !important; }
div[data-testid="bot"] p  { margin: 0 0 10px !important; }

/* ── INPUT ── */
.input-wrap { margin-top: 12px; }

.input-wrap textarea {
    background: #1e261e !important;
    border: 1px solid var(--border-bright) !important;
    border-radius: 2px !important;
    color: var(--accent) !important;
    font-family: var(--font-mono) !important;
    font-size: 13px !important;
    padding: 14px 18px !important;
    resize: none !important;
    caret-color: var(--accent) !important;
    transition: border-color 0.15s, box-shadow 0.15s !important;
}

.input-wrap textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 1px var(--accent), 0 0 15px var(--accent-glow) !important;
    outline: none !important;
}

.input-wrap textarea::placeholder { color: var(--green-muted) !important; }

/* ── BOTONES ── */
.btn-send {
    background: transparent !important;
    color: var(--accent) !important;
    border: 1px solid var(--accent) !important;
    border-radius: 2px !important;
    font-family: var(--font-mono) !important;
    font-size: 12px !important;
    letter-spacing: 2px !important;
    padding: 0 24px !important;
    height: 48px !important;
    cursor: pointer !important;
    text-shadow: 0 0 8px var(--accent) !important;
    box-shadow: 0 0 10px rgba(0,255,65,0.1) !important;
    transition: all 0.15s !important;
    text-transform: uppercase !important;
}

.btn-send:hover {
    background: var(--accent-dark) !important;
    box-shadow: 0 0 20px var(--accent-glow) !important;
    color: var(--green-bright) !important;
}

.btn-clear {
    background: transparent !important;
    color: var(--green-dim) !important;
    border: 1px solid var(--border-bright) !important;
    border-radius: 2px !important;
    font-family: var(--font-mono) !important;
    font-size: 10px !important;
    letter-spacing: 2px !important;
    cursor: pointer !important;
    transition: all 0.15s !important;
    text-transform: uppercase !important;
}

.btn-clear:hover {
    border-color: var(--green-dim) !important;
    color: var(--accent) !important;
}

/* ── EJEMPLOS ── */
.examples-wrap { margin-top: 24px; }

.examples-title {
    font-family: var(--font-mono) !important;
    font-size: 10px !important;
    color: var(--green-dim) !important;
    letter-spacing: 3px !important;
    text-transform: uppercase !important;
    margin-bottom: 10px !important;
}

.gr-samples-table td {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 2px !important;
    color: var(--green-dim) !important;
    font-size: 11px !important;
    font-family: var(--font-mono) !important;
    padding: 8px 12px !important;
    cursor: pointer !important;
    transition: all 0.1s !important;
}

.gr-samples-table td:hover {
    background: var(--accent-dark) !important;
    border-color: var(--accent-dim) !important;
    color: var(--accent) !important;
    text-shadow: 0 0 6px var(--accent) !important;
}

/* ── FOOTER ── */
.footer-wrap {
    border-top: 1px solid var(--border);
    padding: 14px 40px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.footer-stack {
    font-family: var(--font-mono);
    font-size: 10px;
    color: var(--green-muted);
    letter-spacing: 1px;
}

.footer-stack span { color: var(--green-dim); }

.footer-author {
    font-family: var(--font-mono);
    font-size: 10px;
    color: var(--green-muted);
    letter-spacing: 1px;
}

footer { display: none !important; }
.built-with { display: none !important; }
"""

# ── HTML estático ───────────────────────────────────────────────────
HEADER_HTML = """
<div class="header-wrap">
  <div class="header-top">
    <div class="status-dot"></div>
    <div class="header-title">SUPPORT_ASSISTANT.RAG</div>
  </div>
  <div class="header-sub">// Customer Operations Playbook · Cristian Ursan</div>
  <div class="header-meta">
    <div class="meta-chip">modelo <span>llama3.2</span></div>
    <div class="meta-chip">GPU <span>RTX_5070_Ti</span></div>
    <div class="meta-chip">docs <span>9_caps</span></div>
    <div class="meta-chip">memoria <span>ON</span></div>
    <div class="meta-chip">stream <span>ON</span></div>
  </div>
</div>
"""

FOOTER_HTML = """
<div class="footer-wrap">
  <div class="footer-stack">
    <span>LangChain</span> · <span>Llama_3.2</span> · <span>ChromaDB</span> ·
    <span>sentence-transformers</span> · <span>CUDA</span> · <span>Gradio</span>
  </div>
  <div class="footer-author">© 2026 Cristian Ursan</div>
</div>
"""


# ── Lógica de chat con streaming ───────────────────────────────────
def chat_stream(message: str, history: list):
    """Generador que emite tokens en tiempo real."""
    if not message.strip():
        yield history
        return

    # Añadir mensajes al historial
    history = history + [
        {"role": "user",      "content": message},
        {"role": "assistant", "content": ""},
    ]
    yield history

    try:
        assistant = get_assistant()
        sources   = []

        for token in assistant.ask_stream(message):
            # El último yield del generador es el dict de fuentes
            if isinstance(token, dict) and "__sources__" in token:
                sources = token["__sources__"]
                break
            history[-1]["content"] += token
            yield history

        # Añadir fuentes al final de la respuesta
        if sources:
            src_list = " · ".join(f"`{s}`" for s in sorted(sources))
            history[-1]["content"] += f"\n\n---\n📚 **Fuentes:** {src_list}"
            yield history

    except FileNotFoundError:
        history[-1]["content"] = "⚠️ Playbook no indexado. Ejecuta `python src/ingest.py` primero."
        yield history
    except ConnectionError:
        history[-1]["content"] = "⚠️ Ollama no disponible. Ejecuta `ollama serve`."
        yield history
    except Exception as e:
        history[-1]["content"] = f"❌ Error: {str(e)}"
        yield history


# ── Interfaz Gradio ─────────────────────────────────────────────────
def build_interface() -> gr.Blocks:
    with gr.Blocks(
        title="Support Assistant RAG",
        css=CUSTOM_CSS,
        theme=gr.themes.Base(
            primary_hue="green",
            neutral_hue="slate",
            font=gr.themes.GoogleFont("Share Tech Mono"),
        ),
    ) as demo:

        gr.HTML(HEADER_HTML)

        with gr.Column(elem_classes="main-wrap"):

            chatbot = gr.Chatbot(
                label="",
                height=480,
                show_label=False,
                elem_classes="chatbot-wrap",
                type="messages",
            )

            with gr.Row(elem_classes="input-wrap"):
                msg = gr.Textbox(
                    placeholder="$ ingresa tu pregunta sobre Customer Operations...",
                    label="",
                    show_label=False,
                    scale=5,
                    lines=1,
                    max_lines=4,
                    autofocus=True,
                )
                send_btn = gr.Button(
                    "[ EJECUTAR ]",
                    variant="primary",
                    scale=1,
                    elem_classes="btn-send",
                )

            with gr.Row():
                clear_btn = gr.Button(
                    "[ CLEAR ]",
                    variant="secondary",
                    elem_classes="btn-clear",
                )

            with gr.Column(elem_classes="examples-wrap"):
                gr.HTML('<div class="examples-title">// queries de ejemplo</div>')
                gr.Examples(
                    examples=EXAMPLE_QUESTIONS,
                    inputs=msg,
                    label="",
                )

        gr.HTML(FOOTER_HTML)

        # ── Handlers ──
        def respond(message, history):
            if not message.strip():
                return "", history
            for updated_history in chat_stream(message, history):
                yield "", updated_history

        def clear_conversation():
            try:
                get_assistant().reset_memory()
            except Exception:
                pass
            return [], ""

        msg.submit(respond,          [msg, chatbot], [msg, chatbot])
        send_btn.click(respond,      [msg, chatbot], [msg, chatbot])
        clear_btn.click(clear_conversation, None,   [chatbot, msg])

    return demo


# ── Entry point ─────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "═" * 55)
    print("  SUPPORT ASSISTANT RAG  ·  v2.1")
    print("  Customer Operations Playbook · Cristian Ursan")
    print("═" * 55)
    print("  Iniciando sistema...\n")

    demo = build_interface()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True,
    )
