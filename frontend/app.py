import ast
import os

import black
import requests
import streamlit as st

try:
    from streamlit_ace import st_ace
except ImportError:
    st_ace = None


BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


def syntax_error_details(exc: SyntaxError, code: str) -> dict[str, str | int]:
    line_number = exc.lineno or 1
    lines = code.splitlines()
    line_text = exc.text or (lines[line_number - 1] if line_number <= len(lines) else "")

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
    except black.InvalidInput as exc:
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
            st.code(f"{format_error['text']}\n{caret_padding}^", language="python")


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


st.set_page_config(page_title="AI Coding POC", page_icon=":computer:", layout="wide")
st.title("AI-Assisted Coding Tool (POC)")
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
        st.caption("Install streamlit-ace for full editor mode. Using basic text area for now.")
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
        formatted_code, format_error = format_python_code(st.session_state.code_buffer)

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
        st.subheader("Generated Code Preview")
        st.code(st.session_state.generated_code, language="python")

        if st.button("Insert Into Code"):
            snippet = st.session_state.generated_code.strip()

            if snippet:
                st.session_state.code_buffer = snippet
                st.session_state.editor_content = snippet
                st.session_state.format_error = None
                st.session_state.last_inserted_code = snippet
                st.session_state.editor_version += 1
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
        height=140,
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
            st.session_state.pending_index = len(st.session_state.chat_history) - 1
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
                    "current_code": st.session_state.code_buffer,
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
