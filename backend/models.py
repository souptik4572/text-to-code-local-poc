from pydantic import BaseModel


class GenerateRequest(BaseModel):
    current_code: str = ""
    instruction: str


class GenerateResponse(BaseModel):
    generated_code: str
