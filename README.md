# Support Assistant RAG
> Customer Operations Playbook · Cristian Ursan · Marzo 2026

Chatbot inteligente que responde preguntas sobre Customer Operations usando
RAG (Retrieval-Augmented Generation) con GPU local (RTX 5070 Ti).

---

## Stack

| Componente | Tecnología |
|---|---|
| Embeddings | `sentence-transformers` (GPU/CUDA) |
| Vector DB | ChromaDB (local) |
| LLM | Llama 3.2 via Ollama (GPU) |
| Framework | LangChain |
| Interface | Gradio |

---

## Setup (Windows + WSL2 o PowerShell)

### 1. Prerrequisitos

```bash
# Verifica Python
python --version   # necesitas 3.10+

# Verifica CUDA (en PowerShell o WSL)
nvidia-smi
```

### 2. Clonar / crear carpeta del proyecto

```bash
git init support-assistant-rag
cd support-assistant-rag
```

### 3. Crear entorno virtual

```bash
python -m venv venv

# Windows PowerShell
.\venv\Scripts\Activate.ps1

# WSL / Linux
source venv/bin/activate
```

### 4. Instalar dependencias

```bash
pip install -r requirements.txt
```

> ⚠️ PyTorch con CUDA 12.x (RTX 5070 Ti):
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
```

### 5. Instalar Ollama y descargar Llama 3.2

```bash
# Descarga Ollama desde https://ollama.com
# Luego en terminal:
ollama pull llama3.2
```

### 6. Verificar CUDA

```python
python -c "import torch; print('CUDA:', torch.cuda.is_available(), '|', torch.cuda.get_device_name(0))"
```

Debe mostrar: `CUDA: True | NVIDIA GeForce RTX 5070 Ti`

---

## Uso

### Paso 1: Indexar el Playbook

```bash
python src/ingest.py
```

Esto carga los `.md` de `/playbook`, genera embeddings con GPU y los
guarda en ChromaDB (carpeta `/chroma_db`).

### Paso 2: Lanzar el Asistente

```bash
python src/app.py
```

Abre el navegador en `http://localhost:7860`

---

## Estructura del Proyecto

```
support-assistant-rag/
├── README.md
├── requirements.txt
├── .env.example
├── src/
│   ├── ingest.py       # Carga documentos → embeddings → ChromaDB
│   ├── rag.py          # Pipeline RAG (LangChain + Ollama)
│   └── app.py          # Interfaz Gradio
├── playbook/
│   ├── 01_gestion_equipos_internacionales.md
│   ├── 02_kpis_metricas.md
│   ├── 03_procesos_escalado.md
│   └── ...
└── chroma_db/          # Generado automáticamente tras ingest.py
```

---

## Añadir contenido al Playbook

Crea archivos `.md` en `/playbook/` siguiendo el formato de los
existentes. Luego vuelve a ejecutar `python src/ingest.py` para
re-indexar.

---

## Demo para Entrevistas

El agente puede responder preguntas como:
- *"¿Cuál es el proceso de escalado para clientes premium?"*
- *"¿Qué KPIs usas para medir la performance de un equipo de soporte?"*
- *"¿Cómo gestionas onboarding de agentes en equipos remotos?"*

Ideal para mostrar en entrevistas en NTT DATA, Allianz, etc.
