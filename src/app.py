"""
app.py
------
Interfaz web Gradio para el Support Assistant RAG.

Uso:
    python src/app.py
    → Abre http://localhost:7860
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import gradio as gr
from src.rag import get_assistant

# Preguntas de ejemplo para la demo
EXAMPLE_QUESTIONS = [
    "¿Cuál es el proceso de escalado para clientes premium?",
    "¿Qué KPIs usas para medir la performance de un equipo de soporte?",
    "¿Cómo defines las prioridades de tickets según el SLA?",
    "¿Cómo haces el onboarding de un nuevo agente de soporte?",
    "¿Qué métricas de calidad usas en el QA de soporte?",
    "¿Cómo gestionas un equipo distribuido en múltiples zonas horarias?",
]


def chat(message: str, history: list) -> str:
    """Función principal del chatbot."""
    if not message.strip():
        return "Por favor, escribe una pregunta."

    try:
        assistant = get_assistant()
        result    = assistant.ask(message)

        answer  = result["answer"]
        sources = result["sources"]

        # Formatea las fuentes al final de la respuesta
        if sources:
            source_names = [os.path.basename(s) for s in sources]
            answer += f"\n\n---\n📚 **Fuentes:** {', '.join(source_names)}"

        return answer

    except FileNotFoundError:
        return (
            "⚠️ El playbook no está indexado. Ejecuta primero:\n\n"
            "```\npython src/ingest.py\n```"
        )
    except ConnectionError:
        return (
            "⚠️ No se puede conectar con Ollama. Asegúrate de que está corriendo:\n\n"
            "```\nollama serve\n```"
        )
    except Exception as e:
        return f"❌ Error: {str(e)}"


def build_interface() -> gr.Blocks:
    with gr.Blocks(
        title="Support Assistant RAG",
        theme=gr.themes.Soft(primary_hue="blue"),
    ) as demo:

        gr.Markdown(
            """
            # 🤖 Support Assistant RAG
            ### Customer Operations Playbook · Cristian Ursan
            
            Asistente especializado en Customer Operations con 12+ años de experiencia documentada.
            Basado en RAG con GPU local (RTX 5070 Ti).
            """
        )

        chatbot = gr.Chatbot(
            label="Conversación",
            height=450,
            show_label=False,
        )

        with gr.Row():
            msg = gr.Textbox(
                placeholder="Pregunta sobre Customer Operations, KPIs, escalados, SLAs...",
                label="Tu pregunta",
                scale=4,
                autofocus=True,
            )
            send_btn = gr.Button("Enviar", variant="primary", scale=1)

        with gr.Row():
            clear_btn = gr.Button("🗑️ Limpiar conversación", variant="secondary")

        gr.Examples(
            examples=EXAMPLE_QUESTIONS,
            inputs=msg,
            label="💡 Preguntas de ejemplo",
        )

        gr.Markdown(
            """
            ---
            *Stack: LangChain · Llama 3.2 (Ollama) · ChromaDB · sentence-transformers · CUDA*
            """
        )

        # Lógica del chat
        def respond(message, history):
            reply = chat(message, history)
            history.append((message, reply))
            return "", history

        msg.submit(respond, [msg, chatbot], [msg, chatbot])
        send_btn.click(respond, [msg, chatbot], [msg, chatbot])
        clear_btn.click(lambda: ([], ""), None, [chatbot, msg])

    return demo


if __name__ == "__main__":
    print("🚀 Iniciando Support Assistant RAG...")
    print("   Cargando modelo (primera vez puede tardar ~30s)...\n")

    demo = build_interface()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True,
    )
