# CodeLens AI

CodeLens AI is a multi-agent code review application. It combines a Streamlit interface, a FastAPI backend, Azure OpenAI for review and chat, and a local BGE embedding model with a FAISS knowledge base.

Users can submit code by pasting it into the application, uploading a file or ZIP archive, or providing a GitHub file or pull-request URL. Reviews include security, architecture, and performance findings, with a chat interface for follow-up questions.

## Requirements

- Python 3.10 or later
- An Azure OpenAI resource with a deployed chat model
- Network access to download Python packages and, if needed, the embedding model

The application uses local file storage and a local FAISS index by default. PostgreSQL is not required for local development.

## Setup

Run these commands from the repository root.

### 1. Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

On Windows PowerShell, activate it with:

```powershell
.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Installing the ML dependencies, including PyTorch and FAISS, may take a few minutes and require several gigabytes of free disk space.

### 3. Configure Azure OpenAI

Create a `.env` file in the repository root:

```dotenv
AZURE_OPENAI_API_KEY=your-azure-openai-api-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=your-chat-model-deployment
AZURE_OPENAI_API_VERSION=2024-10-21

# Optional: used when accessing private GitHub repositories or for higher API limits.
GITHUB_TOKEN=your-github-token
```

Use the deployment name configured in your Azure OpenAI resource, not just the model family name. `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, and `AZURE_OPENAI_DEPLOYMENT_NAME` are required. The API version defaults to `2024-10-21` if omitted. Keep `.env` private and do not commit credentials.

### 4. Download the embedding model

The application loads `BAAI/bge-small-en-v1.5` from `media/models/bge-small-en-v1.5` by default. Download the complete model snapshot before starting the application. The repository contains some model assets, but not the full checkpoint required by the default Sentence Transformers loader. Run this from the repository root:

```bash
python - <<'PY'
from huggingface_hub import snapshot_download

snapshot_download(
    repo_id="BAAI/bge-small-en-v1.5",
    local_dir="media/models/bge-small-en-v1.5",
)
PY
```

To use a different local model directory, set `EMBEDDING_MODEL_NAME` in `.env` to that path. The configured model must be compatible with Sentence Transformers.

### 5. (Optional) Rebuild the knowledge index

The repository includes a FAISS index at `media/vector_store/`. If you add or update Markdown files under `media/knowledge_base/`, rebuild the index:

```bash
python scripts/ingest_knowledge.py
```

This command creates embeddings using the configured local model and replaces the index under `media/vector_store/`.

## Run the application

The frontend and backend are separate processes. Start each in its own terminal, with the virtual environment activated in both.

**Terminal 1 — FastAPI backend**

```bash
uvicorn src.main:app --reload --host 127.0.0.1 --port 8000
```

The API is available at <http://127.0.0.1:8000>, and its interactive documentation is at <http://127.0.0.1:8000/docs>. The root endpoint returns a health status.

**Terminal 2 — Streamlit frontend**

```bash
streamlit run streamlit_app.py
```

Open the local URL printed by Streamlit, normally <http://localhost:8501>. The frontend connects to the backend at `http://127.0.0.1:8000`.

## Configuration reference

| Variable | Required | Description |
| --- | --- | --- |
| `AZURE_OPENAI_API_KEY` | Yes | API key for the Azure OpenAI resource |
| `AZURE_OPENAI_ENDPOINT` | Yes | Azure OpenAI resource endpoint |
| `AZURE_OPENAI_DEPLOYMENT_NAME` | Yes | Azure deployment name used for chat and review |
| `AZURE_OPENAI_API_VERSION` | No | Azure API version; defaults to `2024-10-21` |
| `EMBEDDING_MODEL_NAME` | No | Local Sentence Transformers model path; defaults to `./media/models/bge-small-en-v1.5` |
| `GITHUB_TOKEN` | No | GitHub token for private repositories or higher API limits |
| `DATABASE_URL` | No | Optional database configuration; local development uses file storage by default |
| `MEDIA_DIR` | No | Media directory; defaults to `./media` |

## Project layout

```text
streamlit_app.py          Streamlit user interface
src/main.py               FastAPI application entry point
src/agents/               Review and chat agents
src/graph/                Review workflow graph
src/rag/                  Knowledge-base chunking and FAISS retrieval
media/knowledge_base/     Security, architecture, and performance guidance
media/models/             Local embedding model
media/vector_store/       FAISS index
media/sessions/           Local session and review data
scripts/ingest_knowledge.py  Rebuild the local knowledge index
```

## Troubleshooting

- **Missing Azure settings:** Confirm `.env` is in the repository root and contains all three required Azure values.
- **Azure authentication or deployment errors:** Verify the endpoint, API key, API version, and deployment name in the Azure portal.
- **Embedding model not found:** Run the model download command from the repository root, or set `EMBEDDING_MODEL_NAME` to the correct local path.
- **Frontend cannot connect:** Start the FastAPI backend first and confirm that it is listening on `127.0.0.1:8000`.
- **No relevant knowledge results:** Confirm that `media/vector_store/` contains the FAISS index files. Rebuild it with `python scripts/ingest_knowledge.py` if the knowledge base has changed.
