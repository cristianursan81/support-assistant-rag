"""
app.py  ·  v2.0
---------------
Interfaz premium para Support Assistant RAG.
Diseño: Ops Dashboard — dark, profesional, listo para entrevistas.
"""

import sys
import os
import time
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import gradio as gr
from src.rag import get_assistant

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

CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:ital,wght@0,400;0,700;1,400&family=DM+Sans:wght@300;400;500;600&display=swap');

:root {
    --bg-primary:    #090c10;
    --bg-secondary:  #0f1318;
    --bg-card:       #141920;
    --bg-hover:      #1a2030;
    --border:        #1e2a3a;
    --border-bright: #243040;
    --accent:        #00d4ff;
    --accent-dim:    #0090b3;
    --accent-glow:   rgba(0, 212, 255, 0.12);
    --green:         #00ff88;
    --green-dim:     #00cc6a;
    --amber:         #ffb800;
    --text-primary:  #e8edf5;
    --text-secondary:#8a9bb5;
    --text-muted:    #4a5a70;
    --font-mono:     'Space Mono', monospace;
    --font-sans:     'DM Sans', sans-serif;
}

* { box-sizing: border-box; }

body, .gradio-container {
    background: var(--bg-primary) !important;
    font-family: var(--font-sans) !important;
    color: var(--text-primary) !important;
}

.gradio-container {
    max-width: 1100px !important;
    margin: 0 auto !important;
    padding: 0 !important;
}

/* ── HEADER ── */
.header-wrap {
    padding: 40px 40px 0;
    border-bottom: 1px solid var(--border);
    margin-bottom: 0;
}

.header-top {
    display: flex;
    align-items: center;
    gap: 16px;
    margin-bottom: 8px;
}

.status-dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    background: var(--green);
    box-shadow: 0 0 8px var(--green);
    animation: pulse 2s ease-in-out infinite;
    flex-shrink: 0;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.4; }
}

.header-title {
    font-family: var(--font-mono) !important;
    font-size: 22px !important;
    font-weight: 700 !important;
    color: var(--accent) !important;
    letter-spacing: -0.5px;
    margin: 0 !important;
    line-height: 1 !important;
}

.header-sub {
    font-size: 12px !important;
    color: var(--text-muted) !important;
    font-family: var(--font-mono) !important;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin: 0 0 20px !important;
    padding-left: 24px;
}

.header-meta {
    display: flex;
    gap: 24px;
    padding: 14px 0;
    border-top: 1px solid var(--border);
}

.meta-chip {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 11px;
    font-family: var(--font-mono);
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 1px;
}

.meta-chip span {
    color: var(--accent);
    font-weight: 700;
}

/* ── MAIN LAYOUT ── */
.main-wrap {
    padding: 24px 40px 40px;
}

/* ── CHATBOT ── */
.chatbot-wrap .label-wrap { display: none !important; }

.chatbot-wrap > div {
    background: var(--bg-secondary) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    overflow: hidden !important;
}

/* Mensajes del usuario */
.message.user, div[data-testid="user"] {
    background: #1a2535 !important;
    border: 1px solid #2a3a55 !important;
    border-radius: 10px 10px 2px 10px !important;
    color: #e8edf5 !important;
    font-family: var(--font-sans) !important;
    font-size: 14px !important;
    line-height: 1.6 !important;
    padding: 14px 18px !important;
}

/* Mensajes del asistente */
.message.bot, div[data-testid="bot"] {
    background: #0f1820 !important;
    border: 1px solid #1e2a3a !important;
    border-left: 3px solid var(--accent) !important;
    border-radius: 2px 10px 10px 10px !important;
    color: #e8edf5 !important;
    font-family: var(--font-sans) !important;
    font-size: 14px !important;
    line-height: 1.75 !important;
    padding: 16px 20px !important;
}

/* Forzar color de texto en todos los elementos internos */
.message p, .message li, .message span,
div[data-testid="bot"] p, div[data-testid="bot"] li,
div[data-testid="bot"] span, div[data-testid="bot"] div {
    color: #e8edf5 !important;
}

div[data-testid="bot"] strong, .message.bot strong {
    color: #00d4ff !important;
    font-weight: 600 !important;
}

div[data-testid="bot"] code, .message.bot code {
    background: #050a10 !important;
    color: #00ff88 !important;
    font-family: var(--font-mono) !important;
    padding: 2px 6px !important;
    border-radius: 4px !important;
    font-size: 12px !important;
}

div[data-testid="bot"] ul, div[data-testid="bot"] ol {
    padding-left: 20px !important;
    margin: 8px 0 !important;
}

div[data-testid="bot"] li { margin-bottom: 6px !important; }
div[data-testid="bot"] p { margin: 0 0 10px !important; }

/* ── INPUT ── */
.input-wrap { margin-top: 12px; }

.input-wrap textarea {
    background: var(--bg-secondary) !important;
    border: 1px solid var(--border-bright) !important;
    border-radius: 10px !important;
    color: var(--text-primary) !important;
    font-family: var(--font-sans) !important;
    font-size: 14px !important;
    padding: 14px 18px !important;
    resize: none !important;
    transition: border-color 0.2s ease !important;
}

.input-wrap textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px var(--accent-glow) !important;
    outline: none !important;
}

.input-wrap textarea::placeholder {
    color: var(--text-muted) !important;
}

/* ── BOTONES ── */
.btn-send {
    background: var(--accent) !important;
    color: #000 !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: var(--font-mono) !important;
    font-size: 13px !important;
    font-weight: 700 !important;
    letter-spacing: 1px !important;
    padding: 0 28px !important;
    height: 48px !important;
    cursor: pointer !important;
    transition: all 0.2s ease !important;
    text-transform: uppercase !important;
}

.btn-send:hover {
    background: #33ddff !important;
    box-shadow: 0 0 20px var(--accent-glow) !important;
    transform: translateY(-1px) !important;
}

.btn-clear {
    background: transparent !important;
    color: var(--text-muted) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    font-family: var(--font-mono) !important;
    font-size: 11px !important;
    letter-spacing: 1px !important;
    cursor: pointer !important;
    transition: all 0.2s ease !important;
    text-transform: uppercase !important;
}

.btn-clear:hover {
    border-color: var(--text-muted) !important;
    color: var(--text-secondary) !important;
}

/* ── EJEMPLOS ── */
.examples-wrap { margin-top: 28px; }

.examples-title {
    font-family: var(--font-mono) !important;
    font-size: 10px !important;
    color: var(--text-muted) !important;
    letter-spacing: 3px !important;
    text-transform: uppercase !important;
    margin-bottom: 12px !important;
}

.examples-grid {
    display: grid !important;
    grid-template-columns: repeat(2, 1fr) !important;
    gap: 8px !important;
}

/* Botones de ejemplos de Gradio */
.gr-samples-table td {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    color: var(--text-secondary) !important;
    font-size: 12px !important;
    font-family: var(--font-sans) !important;
    padding: 10px 14px !important;
    cursor: pointer !important;
    transition: all 0.15s ease !important;
}

.gr-samples-table td:hover {
    background: var(--bg-hover) !important;
    border-color: var(--accent-dim) !important;
    color: var(--text-primary) !important;
}

/* ── FOOTER ── */
.footer-wrap {
    border-top: 1px solid var(--border);
    padding: 16px 40px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.footer-stack {
    font-family: var(--font-mono);
    font-size: 10px;
    color: var(--text-muted);
    letter-spacing: 1px;
}

.footer-stack span { color: var(--accent-dim); }

.footer-author {
    font-family: var(--font-mono);
    font-size: 10px;
    color: var(--text-muted);
    letter-spacing: 1px;
}

/* Ocultar elementos de Gradio que no queremos */
footer { display: none !important; }
.built-with { display: none !important; }
#component-0 > div.svelte-1ed2p3z { padding: 0 !important; }
"""

HEADER_HTML = """
<div class="header-wrap">
  <div class="header-top">
    <div class="status-dot"></div>
    <div class="header-title">SUPPORT ASSISTANT RAG</div>
  </div>
  <div class="header-sub">Customer Operations Playbook · Cristian Ursan</div>
  <div class="header-meta">
    <div class="meta-chip">modelo <span>llama3.2</span></div>
    <div class="meta-chip">GPU <span>RTX 5070 Ti</span></div>
    <div class="meta-chip">docs <span>9 capítulos</span></div>
    <div class="meta-chip">memoria <span>activa</span></div>
    <div class="meta-chip">stack <span>LangChain · ChromaDB · CUDA</span></div>
  </div>
</div>
"""

FOOTER_HTML = """
<div class="footer-wrap">
  <div class="footer-stack">
    <span>LangChain</span> · <span>Llama 3.2</span> · <span>ChromaDB</span> · 
    <span>sentence-transformers</span> · <span>CUDA</span> · <span>Gradio</span>
  </div>
  <div class="footer-author">© 2026 Cristian Ursan</div>
</div>
"""


def chat(message: str, history: list) -> str:
    if not message.strip():
        return "Por favor, escribe una pregunta."
    try:
        assistant = get_assistant()
        result    = assistant.ask(message)
        answer    = result["answer"]
        sources   = result["sources"]

        if sources:
            src_list = " · ".join(f"`{s}`" for s in sorted(sources))
            answer += f"\n\n---\n📚 **Fuentes:** {src_list}"

        return answer

    except FileNotFoundError:
        return "⚠️ Playbook no indexado. Ejecuta `python src/ingest.py` primero."
    except ConnectionError:
        return "⚠️ Ollama no disponible. Ejecuta `ollama serve`."
    except Exception as e:
        return f"❌ Error: {str(e)}"


def build_interface() -> gr.Blocks:
    with gr.Blocks(
        title="Support Assistant RAG",
        css=CUSTOM_CSS,
        theme=gr.themes.Base(
            primary_hue="cyan",
            neutral_hue="slate",
            font=gr.themes.GoogleFont("DM Sans"),
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
                avatar_images=(None, "https://api.dicebear.com/7.x/bottts-neutral/svg?seed=ops"),
            )

            with gr.Row(elem_classes="input-wrap"):
                msg = gr.Textbox(
                    placeholder="Pregunta sobre Customer Operations, KPIs, escalados, SLAs, crisis...",
                    label="",
                    show_label=False,
                    scale=5,
                    lines=1,
                    max_lines=4,
                    autofocus=True,
                )
                send_btn = gr.Button(
                    "Enviar →",
                    variant="primary",
                    scale=1,
                    elem_classes="btn-send",
                )

            with gr.Row():
                clear_btn = gr.Button(
                    "⌫  Nueva conversación",
                    variant="secondary",
                    elem_classes="btn-clear",
                )

            with gr.Column(elem_classes="examples-wrap"):
                gr.HTML('<div class="examples-title">// Preguntas de ejemplo</div>')
                gr.Examples(
                    examples=EXAMPLE_QUESTIONS,
                    inputs=msg,
                    label="",
                )

        gr.HTML(FOOTER_HTML)

        # Lógica
        def respond(message, history):
            if not message.strip():
                return "", history
            reply = chat(message, history)
            history.append({"role": "user", "content": message})
            history.append({"role": "assistant", "content": reply})
            return "", history

        def clear_conversation():
            try:
                assistant = get_assistant()
                assistant.reset_memory()
            except Exception:
                pass
            return [], ""

        msg.submit(respond, [msg, chatbot], [msg, chatbot])
        send_btn.click(respond, [msg, chatbot], [msg, chatbot])
        clear_btn.click(clear_conversation, None, [chatbot, msg])

    return demo


if __name__ == "__main__":
    print("\n" + "═" * 55)
    print("  SUPPORT ASSISTANT RAG  ·  v2.0")
    print("  Customer Operations Playbook · Cristian Ursan")
    print("═" * 55)
    print("  Cargando modelo (primera vez ~30s)...\n")

    demo = build_interface()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True,
        favicon_path=None,
    )
