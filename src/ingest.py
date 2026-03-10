"""
ingest.py
---------
Carga los documentos del Playbook, genera embeddings con GPU
y los indexa en ChromaDB.

Uso:
    python src/ingest.py
"""

import os
import glob
import torch
from pathlib import Path
from dotenv import load_dotenv
from tqdm import tqdm

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader
from langchain_chroma import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

load_dotenv()

PLAYBOOK_PATH = os.getenv("PLAYBOOK_PATH", "./playbook")
CHROMA_PATH   = os.getenv("CHROMA_PATH", "./chroma_db")
COLLECTION    = os.getenv("CHROMA_COLLECTION", "support_playbook")
EMBED_MODEL   = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")


def check_cuda():
    if torch.cuda.is_available():
        gpu = torch.cuda.get_device_name(0)
        print(f"✅ CUDA disponible: {gpu}")
        return "cuda"
    else:
        print("⚠️  CUDA no disponible, usando CPU (más lento)")
        return "cpu"


def load_documents(playbook_path: str) -> list:
    """Carga todos los archivos .md del playbook."""
    md_files = glob.glob(os.path.join(playbook_path, "**/*.md"), recursive=True)
    md_files += glob.glob(os.path.join(playbook_path, "*.md"))

    if not md_files:
        raise FileNotFoundError(
            f"No se encontraron archivos .md en '{playbook_path}'. "
            "Añade contenido al playbook primero."
        )

    docs = []
    print(f"\n📂 Cargando {len(md_files)} documentos del playbook...")
    for path in tqdm(md_files):
        loader = TextLoader(path, encoding="utf-8")
        docs.extend(loader.load())

    print(f"✅ {len(docs)} documentos cargados")
    return docs


def split_documents(docs: list) -> list:
    """
    Divide los documentos en chunks optimizados para RAG.
    chunk_size=800 / overlap=100 funciona bien para texto de operaciones.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100,
        separators=["\n## ", "\n### ", "\n\n", "\n", " "],
    )
    chunks = splitter.split_documents(docs)
    print(f"📄 {len(chunks)} chunks generados")
    return chunks


def build_vectorstore(chunks: list, device: str) -> Chroma:
    """Genera embeddings y guarda en ChromaDB."""
    print(f"\n🔢 Generando embeddings con {EMBED_MODEL} ({device.upper()})...")

    embeddings = HuggingFaceEmbeddings(
        model_name=EMBED_MODEL,
        model_kwargs={"device": device},
        encode_kwargs={"normalize_embeddings": True},
    )

    # Si ya existe la DB, la elimina para re-indexar limpio
    if Path(CHROMA_PATH).exists():
        import shutil
        shutil.rmtree(CHROMA_PATH)
        print(f"🗑️  ChromaDB anterior eliminada (re-indexando)")

    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name=COLLECTION,
        persist_directory=CHROMA_PATH,
    )

    print(f"✅ ChromaDB creada en '{CHROMA_PATH}' con {len(chunks)} chunks")
    return vectorstore


def main():
    print("=" * 50)
    print("  Support Assistant RAG — Indexación del Playbook")
    print("=" * 50)

    device = check_cuda()
    docs   = load_documents(PLAYBOOK_PATH)
    chunks = split_documents(docs)
    build_vectorstore(chunks, device)

    print("\n🚀 Indexación completa. Ejecuta ahora: python src/app.py")


if __name__ == "__main__":
    main()
