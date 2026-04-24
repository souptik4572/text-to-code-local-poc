from pydantic import BaseModel


class GenerateRequest(BaseModel):
    problem_statement: str = ""
    current_code: str = ""
    instruction: str


class GenerateResponse(BaseModel):
    generated_code: str
