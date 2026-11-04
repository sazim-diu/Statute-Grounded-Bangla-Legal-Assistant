"""Streamlit front end. Run with: streamlit run frontend/app.py
The FastAPI backend must be running (uvicorn backend.main:app --reload)."""
import os
import uuid

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


def api_post(path: str, payload: dict, token: str | None = None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        return requests.post(f"{API_URL}{path}", json=payload, headers=headers, timeout=120)
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


def show_results(data: dict) -> None:
    results = data["results"]
    if not results:
        st.warning("কোনো প্রাসঙ্গিক ধারা পাওয়া যায়নি।")
        return

    st.success(f"{len(results)}টি সংশ্লিষ্ট ধারা পাওয়া গেছে")
    st.caption(
        "নিচের ধারাগুলো প্রশ্নের সঙ্গে অর্থের দিক থেকে সবচেয়ে মিল। এগুলো সরাসরি উত্তর নয়, "
        "মূল আইনের পাঠ। 'মিলের স্কোর' শুধু মিলের মাত্রা দেখায়, ধারাটি সঠিক বা প্রযোজ্য কি না তা নয়।"
    )
    for r in results:
        label = f"{r['rank']}. {r['act_name']} — ধারা {r['section_number']}: {r['title']}"
        with st.expander(label, expanded=(r["rank"] == 1)):
            st.markdown(f"**আইন:** {r['act_name']}  \n**অধ্যায়:** {r['chapter']}  \n"
                        f"**ধারা নম্বর:** {r['section_number']}  \n**মিলের স্কোর:** {r['score']:.2f}")
            st.markdown("**মূল আইনের পাঠ:**")
            st.markdown(r["text"].replace("\n", "  \n"))
            if r.get("source_url"):
                st.markdown(f"উৎস: [{r['source_url']}]({r['source_url']})")

    st.info(f"পাঠের তারিখ (snapshot): {data['snapshot_date']}  \n{data['amendment_notice']}")
    st.warning(data["disclaimer"])


def show_home() -> None:
    user = st.session_state["user"]
    token = st.session_state["token"]
    st.session_state.setdefault("session_id", uuid.uuid4().hex)

    st.title("⚖️ LexBangla")
    top_left, top_right = st.columns([4, 1])
    top_left.write(f"Logged in as **{user['username']}** ({user['role']})")
    if top_right.button("Logout"):
        st.session_state.clear()
        st.rerun()

    st.caption("আপনার নাম, ফোন নম্বর বা ব্যক্তিগত তথ্য লিখবেন না।")
    with st.form("search_form"):
        question = st.text_area("আপনার আইনি প্রশ্ন বাংলায় লিখুন", height=100,
                                placeholder="যেমন: মালিক মাসের বেতন না দিলে শ্রমিক কী করতে পারেন?")
        submitted = st.form_submit_button("খুঁজুন")

    if submitted:
        with st.spinner("খোঁজা হচ্ছে... (প্রথমবার কিছুটা সময় লাগতে পারে)"):
            resp = api_post(
                "/search",
                {"question": question, "session_id": st.session_state["session_id"]},
                token=token,
            )
        if resp is None:
            return
        if resp.status_code == 200:
            st.session_state["last_result"] = resp.json()
        elif resp.status_code == 401:
            st.session_state.clear()
            st.rerun()
        else:
            st.session_state.pop("last_result", None)
            st.error(error_text(resp))

    if "last_result" in st.session_state:
        show_results(st.session_state["last_result"])


if "token" in st.session_state:
    show_home()
else:
    show_auth_forms()
