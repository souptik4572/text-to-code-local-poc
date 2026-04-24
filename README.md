# AI-Assisted Coding Tool (Local POC)

This is a minimal end-to-end POC where:

- Streamlit provides a live editable code editor and instruction input.
- FastAPI exposes a `/generate` endpoint.
- Ollama (Gemma) generates Python code snippets from the instruction + current code.

## Project structure

- `backend/main.py` FastAPI app and `/generate` API
- `backend/models.py` request/response models
- `backend/prompt.py` prompt construction
- `backend/llm.py` Ollama API integration
- `frontend/app.py` Streamlit UI (editor, generate, preview, insert)

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Start Ollama (Gemma)

In one terminal:

```bash
ollama serve
```

In another terminal (first time only):

```bash
ollama pull gemma:latest
```

## Run backend

```bash
uvicorn backend.main:app --reload --port 8000
```

Backend URL: `http://localhost:8000`

## Run frontend

```bash
streamlit run frontend/app.py
```

Frontend URL: `http://localhost:8501`

## Optional environment variables

```bash
export BACKEND_URL=http://localhost:8000
export OLLAMA_URL=http://localhost:11434/api/generate
export OLLAMA_MODEL=gemma:latest
```
