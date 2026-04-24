import os

import requests
import streamlit as st


BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


st.set_page_config(page_title="AI Coding POC", page_icon=":computer:", layout="wide")
st.title("AI-Assisted Coding Tool (POC)")
st.caption(f"Backend URL: {BACKEND_URL}")


if "code_buffer" not in st.session_state:
    st.session_state.code_buffer = ""

if "generated_code" not in st.session_state:
    st.session_state.generated_code = ""

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


left_col, right_col = st.columns([2, 1], gap="large")

with left_col:
    st.subheader("Code Editor")
    edited_code = st.text_area(
        "Live code buffer",
        value=st.session_state.code_buffer,
        height=420,
        placeholder="Your Python code appears here...",
    )
    st.session_state.code_buffer = edited_code

    if st.session_state.generated_code:
        st.subheader("Generated Code Preview")
        st.code(st.session_state.generated_code, language="python")

        if st.button("Insert into Code"):
            current = st.session_state.code_buffer.rstrip()
            snippet = st.session_state.generated_code.strip()
            if current and snippet:
                st.session_state.code_buffer = f"{current}\n\n{snippet}"
            elif snippet:
                st.session_state.code_buffer = snippet
            st.rerun()

with right_col:
    st.subheader("Code Chat")

    if st.session_state.chat_history:
        for item in reversed(st.session_state.chat_history):
            with st.container(border=True):
                st.write(item["instruction"])
                status = item.get("status", "done")
                if status == "generating":
                    st.caption("Generating code...")
                elif status == "error":
                    st.caption(f"Failed: {item.get('error', 'Unknown error')}")
                else:
                    st.caption("Code generated")
    else:
        st.caption("No prompts yet.")

    if st.session_state.clear_instruction_input:
        st.session_state.instruction_input = ""
        st.session_state.clear_instruction_input = False

    st.text_input(
        "Instruction",
        key="instruction_input",
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
