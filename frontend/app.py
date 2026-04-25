import ast
import difflib
import html
import os
import re
from pathlib import Path

import black
import requests
import streamlit as st
from black.parsing import InvalidInput

try:
    from streamlit_ace import st_ace
except ImportError:
    st_ace = None


BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
STATIC_DIR = Path(__file__).parent / "static"


def syntax_error_details(exc: SyntaxError, code: str) -> dict[str, str | int]:
    line_number = exc.lineno or 1
    lines = code.splitlines()
    line_text = exc.text or (
        lines[line_number - 1] if line_number <= len(lines) else "")

    return {
        "line": line_number,
        "column": exc.offset or 1,
        "message": exc.msg,
        "text": line_text.rstrip(),
    }


def format_python_code(code: str) -> tuple[str | None, dict[str, str | int] | None]:
    try:
        ast.parse(code)
        return black.format_str(code, mode=black.FileMode()), None
    except SyntaxError as exc:
        return None, syntax_error_details(exc, code)
    except InvalidInput as exc:
        return None, {
            "line": 1,
            "column": 1,
            "message": str(exc),
            "text": "",
        }


def show_format_error(container, format_error: dict[str, str | int] | None) -> None:
    if not format_error:
        return

    with container.container():
        st.error(
            f"Syntax error on line {format_error['line']}, "
            f"column {format_error['column']}: {format_error['message']}"
        )
        if format_error["text"]:
            caret_padding = " " * (int(format_error["column"]) - 1)
            st.code(
                f"{format_error['text']}\n{caret_padding}^", language="python")


def protected_starter_lines(starter_code: str) -> list[str]:
    if not starter_code.strip():
        return []
    return [
        line
        for line in starter_code.splitlines()
        if line.strip() and line.strip() not in ("pass", "...")
    ]


def starter_violations(
    starter_code: str, current_code: str, generated_code: str
) -> list[str]:
    if not starter_code.strip():
        return []
    starter = protected_starter_lines(starter_code)
    current_lines = set(current_code.splitlines())
    generated_lines = set(generated_code.splitlines())
    return [
        line
        for line in starter
        if line in current_lines and line not in generated_lines
    ]


def _intraline_html(old_line: str, new_line: str, kind: str) -> str:
    old_tokens = re.findall(r"\w+|\W", old_line)
    new_tokens = re.findall(r"\w+|\W", new_line)
    matcher = difflib.SequenceMatcher(a=old_tokens, b=new_tokens, autojunk=False)

    parts: list[str] = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if kind == "old":
            chunk = "".join(old_tokens[i1:i2])
            if not chunk:
                continue
            if tag == "equal":
                parts.append(html.escape(chunk))
            elif tag in ("replace", "delete"):
                parts.append(
                    f'<span class="diff-word-removed">{html.escape(chunk)}</span>'
                )
        else:
            chunk = "".join(new_tokens[j1:j2])
            if not chunk:
                continue
            if tag == "equal":
                parts.append(html.escape(chunk))
            elif tag in ("replace", "insert"):
                parts.append(
                    f'<span class="diff-word-added">{html.escape(chunk)}</span>'
                )
    return "".join(parts)


def _diff_line(marker: str, css_class: str, content_html: str) -> str:
    return (
        f'<div class="diff-line {css_class}">'
        f'<span class="diff-marker">{marker}</span>'
        f'<span class="diff-content">{content_html or "&nbsp;"}</span>'
        f"</div>"
    )


def render_unified_diff(old_code: str, new_code: str) -> str:
    old_lines = old_code.splitlines()
    new_lines = new_code.splitlines()
    matcher = difflib.SequenceMatcher(a=old_lines, b=new_lines, autojunk=False)

    rows: list[str] = ['<div class="diff-container">']
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            for line in old_lines[i1:i2]:
                rows.append(_diff_line(" ", "diff-line-equal", html.escape(line)))
        elif tag == "delete":
            for line in old_lines[i1:i2]:
                rows.append(_diff_line("-", "diff-line-removed", html.escape(line)))
        elif tag == "insert":
            for line in new_lines[j1:j2]:
                rows.append(_diff_line("+", "diff-line-added", html.escape(line)))
        elif tag == "replace":
            old_block = old_lines[i1:i2]
            new_block = new_lines[j1:j2]
            pair_count = max(len(old_block), len(new_block))
            for k in range(pair_count):
                if k < len(old_block):
                    counterpart = new_block[k] if k < len(new_block) else ""
                    inner = _intraline_html(old_block[k], counterpart, "old")
                    rows.append(_diff_line("-", "diff-line-removed", inner))
            for k in range(pair_count):
                if k < len(new_block):
                    counterpart = old_block[k] if k < len(old_block) else ""
                    inner = _intraline_html(counterpart, new_block[k], "new")
                    rows.append(_diff_line("+", "diff-line-added", inner))
    rows.append("</div>")
    return "".join(rows)


def show_chat_item(item: dict[str, str]) -> None:
    with st.container(border=True):
        st.write(item["instruction"])
        status = item.get("status", "done")
        if status == "generating":
            st.caption("Generating code...")
        elif status == "error":
            st.caption(f"Failed: {item.get('error', 'Unknown error')}")
        else:
            st.caption("Code generated")


st.set_page_config(page_title="AI DSA Coding",
                   page_icon=":computer:", layout="wide")

st.markdown(
    """
    <style>
        .block-container { padding-top: 1rem; padding-bottom: 1rem; }
        div[data-testid="stAppViewBlockContainer"] { padding-top: 1rem; }

        .diff-container {
            background: #1d1f21;
            border: 1px solid #2c2f33;
            border-radius: 6px;
            padding: 10px 0;
            font-family: 'Menlo', 'Monaco', 'Consolas', monospace;
            font-size: 13px;
            line-height: 1.55;
            max-height: 520px;
            overflow: auto;
        }
        .diff-line {
            display: flex;
            align-items: flex-start;
            padding: 0 12px;
        }
        .diff-line-equal { background: transparent; }
        .diff-line-removed { background: rgba(204, 102, 102, 0.10); }
        .diff-line-added   { background: rgba(181, 189, 104, 0.10); }
        .diff-marker {
            display: inline-block;
            width: 18px;
            flex-shrink: 0;
            color: #6b6f73;
            user-select: none;
            text-align: center;
        }
        .diff-line-removed .diff-marker { color: #cc6666; }
        .diff-line-added   .diff-marker { color: #b5bd68; }
        .diff-content {
            flex: 1;
            color: #c5c8c6;
            white-space: pre-wrap;
            word-break: break-word;
        }
        .diff-word-removed {
            background: rgba(204, 102, 102, 0.38);
            border-radius: 2px;
        }
        .diff-word-added {
            background: rgba(181, 189, 104, 0.38);
            border-radius: 2px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("AI-Assisted DSA Coding Tool")
st.caption(f"Backend URL: {BACKEND_URL}")


@st.dialog("Archived Chats")
def show_archived_chats(archived_items: list[dict[str, str]]) -> None:
    if not archived_items:
        st.caption("No archived chats yet.")
        return

    for item in reversed(archived_items):
        show_chat_item(item)


if "code_buffer" not in st.session_state:
    st.session_state.code_buffer = ""

if "generated_code" not in st.session_state:
    st.session_state.generated_code = ""

if "last_inserted_code" not in st.session_state:
    st.session_state.last_inserted_code = ""

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "instruction_input" not in st.session_state:
    st.session_state.instruction_input = ""

if "is_generating" not in st.session_state:
    st.session_state.is_generating = False

if "pending_index" not in st.session_state:
    st.session_state.pending_index = None

if "clear_instruction_input" not in st.session_state:
    st.session_state.clear_instruction_input = False

if "editor_content" not in st.session_state:
    st.session_state.editor_content = st.session_state.code_buffer

if "editor_version" not in st.session_state:
    st.session_state.editor_version = 0

if "format_error" not in st.session_state:
    st.session_state.format_error = None

if "problem_statement" not in st.session_state:
    st.session_state.problem_statement = ""

if "selected_problem_file" not in st.session_state:
    st.session_state.selected_problem_file = None

if "starter_code" not in st.session_state:
    st.session_state.starter_code = ""

if "starter_problem_file" not in st.session_state:
    st.session_state.starter_problem_file = None


# ── Problem Statement ──────────────────────────────────────────────────────────
with st.expander("Problem Statement", expanded=True):
    md_files = sorted(STATIC_DIR.glob("*.md")) if STATIC_DIR.exists() else []
    file_names = [f.name for f in md_files]
    display_names = {
        f.name: f.stem.replace("_", " ").replace("-", " ").title()
        for f in md_files
    }

    chosen = st.selectbox(
        "Problem file",
        options=["— select a problem —"] + file_names,
        format_func=lambda x: display_names[x] if x in display_names else x,
        label_visibility="collapsed",
    )

    chosen_file = STATIC_DIR / chosen if chosen in file_names else None
    st.session_state.selected_problem_file = chosen_file
    st.session_state.problem_statement = (
        chosen_file.read_text(encoding="utf-8") if chosen_file else ""
    )

    if st.session_state.starter_problem_file != chosen_file:
        st.session_state.starter_code = ""
        st.session_state.starter_problem_file = None

    if st.session_state.problem_statement:
        st.markdown(st.session_state.problem_statement)

        if chosen_file is not None:
            starter_file = chosen_file.with_suffix(".py")
            if starter_file.exists():
                st.divider()
                if st.button(
                    "Load Starter Code",
                    key=f"load_starter_{chosen}",
                    help="Replaces the editor content with the starter code for this problem.",
                ):
                    starter_raw = starter_file.read_text(encoding="utf-8")
                    formatted, fmt_error = format_python_code(starter_raw)
                    if fmt_error is None and formatted is not None:
                        st.session_state.code_buffer = formatted
                        st.session_state.editor_content = formatted
                        st.session_state.format_error = None
                        st.session_state.editor_version += 1
                        st.session_state.starter_code = formatted
                        st.session_state.starter_problem_file = chosen_file
                        st.rerun()

                if st.session_state.starter_code:
                    st.caption(
                        f"Starter loaded — {len(protected_starter_lines(st.session_state.starter_code))} "
                        f"line(s) are protected from code generation."
                    )
    else:
        st.caption("Select a problem above to render its statement here.")

st.divider()

left_col, right_col = st.columns([2, 1], gap="large")

with left_col:
    st.subheader("Code Editor")
    editor_key = f"live_code_editor_{st.session_state.editor_version}"
    format_clicked = st.button("Format Python Code")
    format_error_container = st.empty()

    if st_ace is not None:
        ace_kwargs = {
            "value": st.session_state.editor_content,
            "language": "python",
            "theme": "tomorrow_night",
            "key": editor_key,
            "height": 420,
            "font_size": 14,
            "tab_size": 4,
            "wrap": True,
            "show_gutter": True,
            "show_print_margin": False,
            "auto_update": True,
            "placeholder": "Your Python code appears here...",
        }
        edited_code = st_ace(**ace_kwargs)
    else:
        st.caption(
            "Install streamlit-ace for full editor mode. Using basic text area for now.")
        edited_code = st.text_area(
            "Live code buffer",
            key=editor_key,
            value=st.session_state.editor_content,
            height=420,
            placeholder="Your Python code appears here...",
        )

    if edited_code is not None:
        if edited_code != st.session_state.code_buffer:
            st.session_state.format_error = None
        st.session_state.editor_content = edited_code
        st.session_state.code_buffer = edited_code

    if format_clicked:
        formatted_code, format_error = format_python_code(
            st.session_state.code_buffer)

        if format_error is not None:
            st.session_state.format_error = format_error
        elif formatted_code is not None:
            st.session_state.code_buffer = formatted_code
            st.session_state.editor_content = formatted_code
            st.session_state.format_error = None
            st.session_state.editor_version += 1
            st.rerun()

    show_format_error(format_error_container, st.session_state.format_error)

    if st.session_state.generated_code:
        st.subheader("Proposed Changes")

        current_code = st.session_state.code_buffer
        proposed_code = st.session_state.generated_code

        violations = starter_violations(
            st.session_state.starter_code, current_code, proposed_code
        )

        if violations:
            st.error(
                "Generated code drops protected starter lines. "
                "Accept is disabled — Reject this and re-prompt."
            )
            with st.expander(f"Missing protected line(s): {len(violations)}"):
                st.code("\n".join(violations), language="python")

        if current_code.strip():
            st.markdown(
                render_unified_diff(current_code, proposed_code),
                unsafe_allow_html=True,
            )
        else:
            st.code(proposed_code, language="python")

        accept_col, reject_col = st.columns(2)
        with accept_col:
            accept_clicked = st.button(
                "Accept",
                type="primary",
                use_container_width=True,
                key="accept_diff",
                disabled=bool(violations),
            )
        with reject_col:
            reject_clicked = st.button(
                "Reject", use_container_width=True, key="reject_diff"
            )

        if accept_clicked:
            snippet = proposed_code.strip()
            if snippet:
                st.session_state.code_buffer = snippet
                st.session_state.editor_content = snippet
                st.session_state.format_error = None
                st.session_state.last_inserted_code = snippet
                st.session_state.editor_version += 1
            st.session_state.generated_code = ""
            st.rerun()

        if reject_clicked:
            st.session_state.generated_code = ""
            st.rerun()

with right_col:
    st.subheader("Code Chat")

    if st.session_state.chat_history:
        recent_chats = st.session_state.chat_history[-2:]
        archived_chats = st.session_state.chat_history[:-2]

        for item in reversed(recent_chats):
            show_chat_item(item)

        if archived_chats and st.button(
            "Show Previous Chats",
            use_container_width=True,
        ):
            show_archived_chats(archived_chats)
    else:
        st.caption("No prompts yet.")

    if st.session_state.clear_instruction_input:
        st.session_state.instruction_input = ""
        st.session_state.clear_instruction_input = False

    st.text_area(
        "Instruction",
        key="instruction_input",
        height=315,
        placeholder="create a hashmap to store frequency of elements",
    )

    if st.session_state.is_generating:
        st.info("Code generation in progress...")

    if st.button(
        "Generate Code",
        type="primary",
        disabled=st.session_state.is_generating,
        use_container_width=True,
    ):
        instruction = st.session_state.instruction_input.strip()
        if not instruction:
            st.warning("Please enter an instruction before generating code.")
        else:
            st.session_state.chat_history.append(
                {
                    "instruction": instruction,
                    "status": "generating",
                }
            )
            st.session_state.pending_index = len(
                st.session_state.chat_history) - 1
            st.session_state.is_generating = True
            st.session_state.clear_instruction_input = True
            st.rerun()


if st.session_state.is_generating and st.session_state.pending_index is not None:
    pending_idx = st.session_state.pending_index
    pending_instruction = st.session_state.chat_history[pending_idx]["instruction"]

    with st.spinner("Generating code..."):
        try:
            response = requests.post(
                f"{BACKEND_URL}/generate",
                json={
                    "problem_statement": st.session_state.problem_statement,
                    "current_code": st.session_state.code_buffer,
                    "starter_code": st.session_state.starter_code,
                    "instruction": pending_instruction,
                },
                timeout=120,
            )
            response.raise_for_status()
            generated_code = response.json().get("generated_code", "")
            st.session_state.generated_code = generated_code
            st.session_state.chat_history[pending_idx]["status"] = "done"
        except requests.RequestException as exc:
            st.session_state.chat_history[pending_idx]["status"] = "error"
            st.session_state.chat_history[pending_idx]["error"] = str(exc)
            st.error(f"Generate request failed: {exc}")
        finally:
            st.session_state.is_generating = False
            st.session_state.pending_index = None
            st.rerun()
