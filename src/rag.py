"""
rag.py  ·  v2.1
---------------
Pipeline RAG con memoria de conversación y streaming de respuestas.
"""

import os
import warnings
import torch
from queue import Queue
from threading import Thread
from typing import Generator
from dotenv import load_dotenv

warnings.filterwarnings("ignore", message=".*capture().*")

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import OllamaLLM
from langchain.prompts import PromptTemplate
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferWindowMemory
from langchain.callbacks.base import BaseCallbackHandler

load_dotenv()

CHROMA_PATH  = os.getenv("CHROMA_PATH", "./chroma_db")
COLLECTION   = os.getenv("CHROMA_COLLECTION", "support_playbook")
EMBED_MODEL  = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
OLLAMA_URL   = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")

SYSTEM_PROMPT = """Eres un asistente experto en Customer Operations con más de 12 años
de experiencia gestionando equipos internacionales en EMEA, LATAM y APAC.
Tu conocimiento proviene del playbook de operaciones documentado por Cristian Ursan.

INSTRUCCIONES:
- Usa ÚNICAMENTE la información del contexto proporcionado para responder.
- Si la información no está en el contexto, dilo claramente sin inventar.
- Responde siempre en español, de forma clara, estructurada y accionable.
- Incluye métricas, KPIs o ejemplos concretos cuando sean relevantes.
- Si la pregunta hace referencia a algo mencionado antes en la conversación, úsalo.
- Usa formato con bullets o numeración cuando ayude a la claridad.

CONTEXTO DEL PLAYBOOK:
{context}

HISTORIAL DE CONVERSACIÓN:
{chat_history}

PREGUNTA ACTUAL:
{question}

RESPUESTA:"""

QA_PROMPT = PromptTemplate(
    input_variables=["context", "chat_history", "question"],
    template=SYSTEM_PROMPT,
)

_DONE = object()


class _StreamingHandler(BaseCallbackHandler):
    """Captura tokens del LLM y los mete en una Queue."""

    def __init__(self, queue: Queue):
        self.queue = queue

    def on_llm_new_token(self, token: str, **kwargs):
        self.queue.put(token)

    def on_llm_end(self, *args, **kwargs):
        self.queue.put(_DONE)

    def on_llm_error(self, error, **kwargs):
        self.queue.put(_DONE)


class SupportAssistant:
    def __init__(self):
        self._embeddings  = None
        self._vectorstore = None
        self._chain       = None
        self._memory      = None
        self._retriever   = None

    def _get_device(self) -> str:
        return "cuda" if torch.cuda.is_available() else "cpu"

    def load(self):
        device = self._get_device()

        self._embeddings = HuggingFaceEmbeddings(
            model_name=EMBED_MODEL,
            model_kwargs={"device": device},
            encode_kwargs={"normalize_embeddings": True},
        )

        self._vectorstore = Chroma(
            collection_name=COLLECTION,
            persist_directory=CHROMA_PATH,
            embedding_function=self._embeddings,
        )

        self._retriever = self._vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 5},
        )

        self._memory = ConversationBufferWindowMemory(
            k=6,
            memory_key="chat_history",
            output_key="answer",
            return_messages=True,
        )

        # LLM sin streaming para compatibilidad con la chain
        llm = OllamaLLM(
            model=OLLAMA_MODEL,
            base_url=OLLAMA_URL,
            temperature=0.1,
            num_predict=1024,
        )

        self._chain = ConversationalRetrievalChain.from_llm(
            llm=llm,
            retriever=self._retriever,
            memory=self._memory,
            combine_docs_chain_kwargs={"prompt": QA_PROMPT},
            return_source_documents=True,
            verbose=False,
        )

        print(f"✅ SupportAssistant v2.1 cargado ({device.upper()}, {OLLAMA_MODEL})")
        print(f"   Streaming: activado · Memoria: 6 interacciones")

    def ask(self, question: str) -> dict:
        """Respuesta estándar sin streaming."""
        if not self._chain:
            raise RuntimeError("Ejecuta .load() primero")
        result = self._chain.invoke({"question": question})
        sources = list({
            os.path.basename(doc.metadata.get("source", "desconocido"))
            for doc in result.get("source_documents", [])
        })
        return {"answer": result["answer"], "sources": sources}

    def ask_stream(self, question: str) -> Generator:
        """
        Genera tokens en tiempo real.
        Yields: str (tokens) y al final dict {"__sources__": [...]}
        """
        if not self._retriever:
            raise RuntimeError("Ejecuta .load() primero")

        # 1. Recuperar contexto relevante
        docs = self._retriever.invoke(question)
        context = "\n\n".join(doc.page_content for doc in docs)
        sources = list({
            os.path.basename(doc.metadata.get("source", "desconocido"))
            for doc in docs
        })

        # 2. Construir historial
        chat_history = ""
        if self._memory:
            for msg in self._memory.chat_memory.messages[-6:]:
                role = "Human" if msg.type == "human" else "AI"
                chat_history += f"{role}: {msg.content}\n"

        # 3. Prompt final
        prompt = QA_PROMPT.format(
            context=context,
            chat_history=chat_history,
            question=question,
        )

        # 4. LLM con streaming
        queue: Queue = Queue()
        handler = _StreamingHandler(queue)
        llm_stream = OllamaLLM(
            model=OLLAMA_MODEL,
            base_url=OLLAMA_URL,
            temperature=0.1,
            num_predict=1024,
            streaming=True,
            callbacks=[handler],
        )

        full_answer = []

        def _run():
            llm_stream.invoke(prompt)

        Thread(target=_run, daemon=True).start()

        # 5. Yield tokens
        while True:
            token = queue.get()
            if token is _DONE:
                break
            full_answer.append(token)
            yield token

        # 6. Guardar en memoria
        answer = "".join(full_answer)
        self._memory.chat_memory.add_user_message(question)
        self._memory.chat_memory.add_ai_message(answer)

        # 7. Yield fuentes al final
        yield {"__sources__": sources}

    def reset_memory(self):
        if self._memory:
            self._memory.clear()


_assistant = None

def get_assistant() -> SupportAssistant:
    global _assistant
    if _assistant is None:
        _assistant = SupportAssistant()
        _assistant.load()
    return _assistant