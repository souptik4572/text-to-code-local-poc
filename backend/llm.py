import os
import re

import ollama


OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b-instruct")


def _strip_fences(text: str) -> str:
    # Remove ```python / ```py / ``` wrappers the model emits despite instructions
    stripped = text.strip()
    match = re.match(r"^```[a-zA-Z]*\n(.*?)```$", stripped, re.DOTALL)
    if match:
        return match.group(1).strip()
    return stripped


def generate_code(prompt: dict) -> str:
    response = ollama.chat(
        model=OLLAMA_MODEL,
        messages=[
            {"role": "system", "content": prompt["system"]},
            {"role": "user", "content": prompt["user"]},
        ],
        options={
            "temperature": 0.0,
            "top_p": 1.0,
            "repeat_penalty": 1.1,
            "num_predict": 256,
        },
    )
    message = response.get("message") if isinstance(response, dict) else getattr(response, "message", None)
    content = message.get("content") if isinstance(message, dict) else getattr(message, "content", "")
    return _strip_fences(content or "")
