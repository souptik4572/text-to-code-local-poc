# FastAPI + Streamlit Starter

This project contains:

- `backend/` for the FastAPI app
- `frontend/` for the Streamlit app
- `requirements.txt` shared by both
- `pyproject.toml` for an additional `uv`-native workflow

## Setup with requirements.txt

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Setup with uv

```bash
uv venv .venv
source .venv/bin/activate
uv sync
```

## Run the backend

```bash
uvicorn backend.app:app --reload --port 5000
```

The backend runs on `http://localhost:5000`.

## Run the frontend

```bash
streamlit run frontend/app.py
```

The frontend runs on `http://localhost:8501`.

## Optional environment variable

If your backend runs elsewhere:

```bash
export BACKEND_URL=http://localhost:5000
```
