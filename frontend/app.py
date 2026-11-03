"""Streamlit front end. Run with: streamlit run frontend/app.py
The FastAPI backend must be running (uvicorn backend.main:app --reload)."""
import os

import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="LexBangla", page_icon="⚖️")


def error_text(resp: requests.Response) -> str:
    """Turn a FastAPI error response into a readable message."""
    try:
        detail = resp.json().get("detail")
    except ValueError:
        return f"Server error ({resp.status_code})"
    if isinstance(detail, list):  # validation errors from Pydantic
        return "\n".join(
            "- " + str(d.get("msg", "")).replace("Value error, ", "") for d in detail
        )
    return str(detail)


def api_post(path: str, payload: dict):
    try:
        return requests.post(f"{API_URL}{path}", json=payload, timeout=10)
    except requests.RequestException:
        st.error("Cannot reach the backend. Is uvicorn running?")
        return None


def show_auth_forms() -> None:
    st.title("⚖️ LexBangla")
    st.caption("Statute-Grounded Bangla Legal Assistant · legal information only, not legal advice")
    tab_login, tab_register = st.tabs(["Login", "Register"])

    with tab_login:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")
        if submitted:
            resp = api_post("/auth/login", {"username": username, "password": password})
            if resp is not None:
                if resp.status_code == 200:
                    data = resp.json()
                    st.session_state["token"] = data["access_token"]
                    st.session_state["user"] = data["user"]
                    st.rerun()
                else:
                    st.error(error_text(resp))

    with tab_register:
        st.caption(
            "Do not use your real name or phone number. Password: 8+ characters with "
            "upper-case, lower-case and a digit."
        )
        with st.form("register_form"):
            username = st.text_input("Choose a username")
            password = st.text_input("Choose a password", type="password")
            confirm = st.text_input("Confirm password", type="password")
            submitted = st.form_submit_button("Create account")
        if submitted:
            if password != confirm:
                st.error("Passwords do not match")
            else:
                resp = api_post("/auth/register", {"username": username, "password": password})
                if resp is not None:
                    if resp.status_code == 201:
                        st.success("Account created. Please log in from the Login tab.")
                    else:
                        st.error(error_text(resp))


def show_home() -> None:
    user = st.session_state["user"]
    st.title("⚖️ LexBangla")
    st.write(f"Logged in as **{user['username']}** ({user['role']})")
    if st.button("Logout"):
        st.session_state.clear()
        st.rerun()
    st.info("Question answering will appear here (retrieval and citations come next).")


if "token" in st.session_state:
    show_home()
else:
    show_auth_forms()
