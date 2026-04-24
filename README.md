# AI-Assisted Coding Tool (Local POC)

A minimal end-to-end proof-of-concept where:

- **Streamlit** provides a live code editor (powered by `streamlit-ace`) and natural-language instruction input.
- **FastAPI** exposes a `/generate` endpoint that builds a prompt and calls Ollama.
- **Ollama** (Gemma) runs locally and generates Python code snippets from the instruction + current editor content.

## Project structure

```
text-to-code-local-poc/
├── backend/
│   ├── main.py        # FastAPI app — GET /health, POST /generate
│   ├── models.py      # Pydantic request/response models
│   ├── prompt.py      # Prompt construction for the LLM
│   └── llm.py         # Ollama API integration
├── frontend/
│   └── app.py         # Streamlit UI (editor, generate, preview, insert)
├── run_app.sh         # One-command launcher for both services
├── pyproject.toml     # Project metadata and dependencies (uv)
└── requirements.txt   # Pip-compatible dependency list
```

## Prerequisites

| Requirement | Version |
|---|---|
| Python | 3.12+ |
| [Ollama](https://ollama.com/download) | latest |
| [uv](https://docs.astral.sh/uv/getting-started/installation/) (recommended) | latest |

## 1. Install Ollama and pull the model

Install Ollama from [ollama.com/download](https://ollama.com/download), then pull the model used by this POC:

```bash
ollama pull gemma4:e2b
```

Keep Ollama running in the background (it starts automatically on most systems after install, or run `ollama serve` manually).

## 2. Set up the Python environment

### Option A — uv (recommended)

```bash
uv sync
```

This reads `pyproject.toml` + `uv.lock` and creates `.venv` automatically.

### Option B — pip

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 3. Run the app

### One command (recommended)

```bash
./run_app.sh
```

This script:
1. Activates `.venv`
2. Starts the FastAPI backend on `http://localhost:8000` via `uvicorn` (with `--reload`)
3. Waits up to 30 seconds for the backend `/health` endpoint to respond
4. Starts the Streamlit frontend on `http://localhost:8501`
5. Shuts down the backend automatically when you `Ctrl+C`

### Manually (two terminals)

**Terminal 1 — backend:**

```bash
source .venv/bin/activate
uvicorn backend.main:app --reload --reload-dir backend --port 8000
```

**Terminal 2 — frontend:**

```bash
source .venv/bin/activate
streamlit run frontend/app.py --server.runOnSave true
```

## Using the tool

1. Open `http://localhost:8501` in your browser.
2. Type a Python instruction in the **Instruction** box on the right (e.g. `create a hashmap to store frequency of elements`).
3. Click **Generate Code** — the backend calls Ollama and returns a code snippet.
4. Review the **Generated Code Preview** that appears below the editor.
5. Click **Insert Into Code** to load the snippet into the editor.
6. Optionally click **Format Python Code** to auto-format with `black`.

The editor supports full syntax highlighting via `streamlit-ace`. If the generated code is ambiguous or the instruction is unclear, the model returns `# NEED_MORE_INFORMATION`.

## API reference

### `GET /health`

Returns `{"status": "ok", "service": "backend"}`. Used by `run_app.sh` to verify the backend is up.

### `POST /generate`

**Request body:**

```json
{
  "instruction": "write a binary search function",
  "current_code": ""
}
```

`current_code` is optional (defaults to `""`). It is passed to the LLM as context so the generated snippet respects what is already in the editor.

**Response:**

```json
{
  "generated_code": "def binary_search(arr, target):\n    ..."
}
```

## Environment variables

All variables have sensible defaults and are optional.

| Variable | Default | Description |
|---|---|---|
| `BACKEND_URL` | `http://localhost:8000` | URL the Streamlit frontend uses to reach the backend |
| `OLLAMA_URL` | `http://localhost:11434/api/generate` | Ollama generate endpoint |
| `OLLAMA_MODEL` | `gemma4:e2b` | Ollama model name |

Export before running, or set inline:

```bash
OLLAMA_MODEL=llama3.2 ./run_app.sh
```
