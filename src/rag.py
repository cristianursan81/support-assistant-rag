"""
rag.py
------
Pipeline RAG: recupera contexto relevante del vector DB
y genera respuestas con Llama 3.2 via Ollama.
"""

import os
import torch
from dotenv import load_dotenv

from langchain_chroma import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_ollama import OllamaLLM
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA

load_dotenv()

CHROMA_PATH  = os.getenv("CHROMA_PATH", "./chroma_db")
COLLECTION   = os.getenv("CHROMA_COLLECTION", "support_playbook")
EMBED_MODEL  = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
OLLAMA_URL   = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")

# Prompt especializado en Customer Operations
SYSTEM_PROMPT = """Eres un asistente experto en Customer Operations con más de 12 años
de experiencia gestionando equipos internacionales en EMEA, LATAM y APAC.
Tu conocimiento proviene del playbook de operaciones documentado.

Usa ÚNICAMENTE la información del contexto proporcionado para responder.
Si la información no está en el contexto, dilo claramente.
Responde siempre en español, de forma clara, estructurada y accionable.
Cuando sea relevante, incluye métricas, KPIs o ejemplos concretos.

CONTEXTO DEL PLAYBOOK:
{context}

PREGUNTA:
{question}

RESPUESTA:"""

PROMPT_TEMPLATE = PromptTemplate(
    input_variables=["context", "question"],
    template=SYSTEM_PROMPT,
)


class SupportAssistant:
    def __init__(self):
        self._embeddings  = None
        self._vectorstore = None
        self._chain       = None

    def _get_device(self) -> str:
        return "cuda" if torch.cuda.is_available() else "cpu"

    def load(self):
        """Carga embeddings, ChromaDB y la cadena RAG."""
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

        llm = OllamaLLM(
            model=OLLAMA_MODEL,
            base_url=OLLAMA_URL,
            temperature=0.1,   # Bajo para respuestas consistentes y factuales
            num_predict=1024,
        )

        retriever = self._vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 5},  # Recupera los 5 chunks más relevantes
        )

        self._chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=retriever,
            chain_type_kwargs={"prompt": PROMPT_TEMPLATE},
            return_source_documents=True,
        )

        print(f"✅ SupportAssistant cargado ({device.upper()}, {OLLAMA_MODEL})")

    def ask(self, question: str) -> dict:
        """
        Realiza una pregunta al asistente.
        Devuelve {'answer': str, 'sources': list[str]}
        """
        if not self._chain:
            raise RuntimeError("Ejecuta .load() primero")

        result = self._chain.invoke({"query": question})

        # Extrae fuentes únicas
        sources = list({
            doc.metadata.get("source", "desconocido")
            for doc in result.get("source_documents", [])
        })

        return {
            "answer": result["result"],
            "sources": sources,
        }


# Singleton para reutilizar en la app
_assistant = None


def get_assistant() -> SupportAssistant:
    global _assistant
    if _assistant is None:
        _assistant = SupportAssistant()
        _assistant.load()
    return _assistant
