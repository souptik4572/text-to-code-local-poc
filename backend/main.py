from fastapi import FastAPI, HTTPException

from backend.llm import generate_code
from backend.models import GenerateRequest, GenerateResponse
from backend.prompt import build_prompt


app = FastAPI(title="AI Coding POC Backend")


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "backend"}


@app.post("/generate", response_model=GenerateResponse)
def generate(payload: GenerateRequest) -> GenerateResponse:
    instruction = payload.instruction.strip()
    if not instruction:
        raise HTTPException(status_code=400, detail="instruction cannot be empty")

    prompt = build_prompt(
        payload.problem_statement,
        payload.current_code,
        instruction,
        payload.starter_code,
    )
    generated_code = generate_code(prompt)
    return GenerateResponse(generated_code=generated_code)
