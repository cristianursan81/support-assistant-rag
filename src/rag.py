"""
rag.py  ·  v2.0
---------------
Pipeline RAG con memoria de conversación, embeddings actualizados
y respuestas contextuales multi-turno.
"""

import os
import warnings
import torch
from dotenv import load_dotenv

# Silenciar warnings de telemetría de ChromaDB
warnings.filterwarnings("ignore", message=".*capture().*")

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings          # ✅ sin deprecation
from langchain_ollama import OllamaLLM
from langchain.prompts import PromptTemplate, ChatPromptTemplate
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferWindowMemory

load_dotenv()

CHROMA_PATH  = os.getenv("CHROMA_PATH", "./chroma_db")
COLLECTION   = os.getenv("CHROMA_COLLECTION", "support_playbook")
EMBED_MODEL  = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
OLLAMA_URL   = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")

# Prompt del sistema — experto en Customer Operations
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


class SupportAssistant:
    def __init__(self):
        self._embeddings  = None
        self._vectorstore = None
        self._chain       = None
        self._memory      = None

    def _get_device(self) -> str:
        return "cuda" if torch.cuda.is_available() else "cpu"

    def load(self):
        """Carga embeddings, ChromaDB, memoria y la cadena RAG."""
        device = self._get_device()

        # Embeddings con la librería actualizada
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
            temperature=0.1,
            num_predict=1024,
        )

        retriever = self._vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 5},
        )

        # Memoria de conversación — recuerda las últimas 6 interacciones
        self._memory = ConversationBufferWindowMemory(
            k=6,
            memory_key="chat_history",
            output_key="answer",
            return_messages=True,
        )

        # Cadena conversacional con memoria
        self._chain = ConversationalRetrievalChain.from_llm(
            llm=llm,
            retriever=retriever,
            memory=self._memory,
            combine_docs_chain_kwargs={"prompt": QA_PROMPT},
            return_source_documents=True,
            verbose=False,
        )

        print(f"✅ SupportAssistant v2.0 cargado ({device.upper()}, {OLLAMA_MODEL})")
        print(f"   Memoria: últimas 6 interacciones")

    def ask(self, question: str) -> dict:
        """
        Pregunta al asistente con memoria de conversación.
        Devuelve {'answer': str, 'sources': list[str]}
        """
        if not self._chain:
            raise RuntimeError("Ejecuta .load() primero")

        result = self._chain.invoke({"question": question})

        sources = list({
            os.path.basename(doc.metadata.get("source", "desconocido"))
            for doc in result.get("source_documents", [])
        })

        return {
            "answer": result["answer"],
            "sources": sources,
        }

    def reset_memory(self):
        """Limpia el historial de conversación."""
        if self._memory:
            self._memory.clear()


# Singleton
_assistant = None

def get_assistant() -> SupportAssistant:
    global _assistant
    if _assistant is None:
        _assistant = SupportAssistant()
        _assistant.load()
    return _assistant
