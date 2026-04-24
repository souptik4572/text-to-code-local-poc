from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


class EchoRequest(BaseModel):
    message: str = ""


app = FastAPI(title="FastAPI Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "backend"}


@app.post("/api/echo")
def echo(payload: EchoRequest):
    message = payload.message.strip()
    return {
        "message": message,
        "length": len(message),
        "service": "backend",
    }
