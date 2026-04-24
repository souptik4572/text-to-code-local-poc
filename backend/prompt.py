def build_prompt(current_code: str, instruction: str) -> str:
    return f"""You are a coding assistant.

STRICT RULES:
- Only generate code for the given instruction
- Do NOT solve the full problem
- Do NOT add extra logic
- Output ONLY code (no explanation)

Current Code:
{current_code}

User Instruction:
{instruction}

Code:
"""
