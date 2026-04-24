import os

import requests
import streamlit as st


BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:5000")


st.set_page_config(page_title="FastAPI + Streamlit Starter", page_icon=":rocket:")
st.title("FastAPI + Streamlit Starter")
st.caption(f"Backend URL: {BACKEND_URL}")


def check_backend_health():
    response = requests.get(f"{BACKEND_URL}/api/health", timeout=5)
    response.raise_for_status()
    return response.json()


def send_message(message: str):
    response = requests.post(
        f"{BACKEND_URL}/api/echo",
        json={"message": message},
        timeout=5,
    )
    response.raise_for_status()
    return response.json()


if st.button("Check backend health"):
    try:
        st.success(check_backend_health())
    except requests.RequestException as exc:
        st.error(f"Unable to reach backend: {exc}")


message = st.text_input("Message", placeholder="Type something to send to FastAPI")

if st.button("Send to backend"):
    try:
        st.json(send_message(message))
    except requests.RequestException as exc:
        st.error(f"Request failed: {exc}")
