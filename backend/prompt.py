import re


_STUB_LINE = re.compile(r"^\s*(pass|\.\.\.)\s*$")


def _protected_lines(starter_code: str) -> list[str]:
    if not starter_code.strip():
        return []
    return [
        line
        for line in starter_code.splitlines()
        if line.strip() and not _STUB_LINE.match(line)
    ]


def build_prompt(
    problem_statement: str,
    current_code: str,
    instruction: str,
    starter_code: str = "",
) -> dict:
    has_stub = bool(current_code.strip()) and bool(
        re.search(r"^\s*(pass|\.\.\.)\s*$", current_code, re.MULTILINE)
    )

    if has_stub:
        output_mode = (
            "REWRITE — existing code contains stub(s). "
            "Output the COMPLETE code with ONLY the stub(s) the instruction targets replaced. "
            "Leave every other stub (pass / ...) untouched. "
            "Preserve all signatures, imports, and non-stub lines verbatim."
        )
    else:
        output_mode = (
            "APPEND — no stubs detected. "
            "Output a standalone snippet containing ONLY what the instruction asks for, "
            "to be placed after the existing code."
        )

    protected = _protected_lines(starter_code)
    if protected:
        protected_block = "\n".join(protected)
        protected_section = f"""
<protected_lines immutable="true">
{protected_block}
</protected_lines>

PROTECTED RULE (highest priority, overrides every other rule):
Every line inside <protected_lines> MUST appear VERBATIM in your output — same text, same indentation, same order.
You MUST NOT rename, retype, reword, reformat, split, merge, or remove any protected line.
You MAY replace stub bodies (`pass` / `...`) and add NEW lines around protected lines.
If the instruction conflicts with a protected line, output exactly: # NEED_MORE_INFORMATION
"""
    else:
        protected_section = ""

    system_content = """You are a deterministic Python code-generation engine for DSA problems.
You execute ONE instruction literally and produce the minimal code that satisfies it — nothing more.
The <instruction> block is the ONLY task.

<rules>
AUTHORITY  : <instruction> is the sole task.
LITERAL    : Execute the instruction exactly as worded. Do not expand "one step" into "the algorithm".
SCOPE      : Implement ONLY what the instruction literally names. No inferred steps, no completions, no look-ahead.
GRANULARITY: If the instruction is a single step, output ONLY that step. Do NOT add surrounding structure.
FORESIGHT  : Knowing the full problem does NOT permit solving beyond the instruction.
OUTPUT     : Raw Python only. No markdown, no fences, no backticks, no comments, no explanations.
CONTEXT    : Respect all existing signatures, imports, and non-stub lines exactly.
STUB_FILL  : Replace ONLY the stub(s) the instruction refers to. Leave all other stubs intact.
MINIMALITY : Smallest valid code. No extra variables, imports, helpers, or return statements beyond what the instruction names.
SAFETY     : No duplicate functions or variables. Preserve indentation and syntax.
AMBIGUITY  : If unclear or underspecified → output exactly one line: # NEED_MORE_INFORMATION
</rules>

<forbidden>
- Adding `return` unless the instruction explicitly says to return something.
- Adding loops, conditionals, or helper functions the instruction does not name.
- Filling stubs the instruction did not reference.
- Emitting anything that is not Python source.
- Writing beyond the literal scope of the instruction even if you know the full solution.
</forbidden>"""

    user_content = f"""<output_mode>
{output_mode}
</output_mode>

<existing_code>
{current_code if current_code.strip() else "# (empty)"}
</existing_code>
{protected_section}
<instruction authoritative="true">
{instruction}
</instruction>

Output raw Python only. Execute ONLY the instruction above. Stop the moment it is satisfied."""

    return {
        "system": system_content,
        "user": user_content,
    }
