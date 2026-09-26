import json
import os
from typing import Dict, List, Tuple

import requests
import streamlit as st


GROQ_BASE_URL = "https://api.groq.com/openai/v1"
DEFAULT_MODELS = [
    "llama-3.1-8b-instant",
    "llama-3.3-70b-versatile",
]

TEMPLATES = {
    "Summarize Text": "Summarize the following text in a few clear bullet points:\n\n",
    "Explain Code": "Explain what this code does, step by step:\n\n",
    "Generate Ideas": "Generate 5 creative ideas for: ",
    "Rewrite Content": "Rewrite the following to be clearer and more concise:\n\n",
    "Translate": "Translate the following into [language]:\n\n",
    "Create Email": "Write a professional email about: ",
    "Brainstorm": "Brainstorm possible approaches to solve this problem: ",
}


def initialise_state() -> None:
    if "sessions" not in st.session_state:
        st.session_state.sessions = {"New chat": []}
    if "active_session" not in st.session_state:
        st.session_state.active_session = "New chat"
    if "draft" not in st.session_state:
        st.session_state.draft = ""
    if st.session_state.pop("clear_draft", False):
        st.session_state.draft = ""
    if "models" not in st.session_state:
        st.session_state.models = []
    if "models_key" not in st.session_state:
        st.session_state.models_key = ""
    if "model_error" not in st.session_state:
        st.session_state.model_error = ""


def api_error(response: requests.Response) -> str:
    try:
        payload = response.json()
        if isinstance(payload, dict):
            error = payload.get("error")
            if isinstance(error, dict) and error.get("message"):
                return str(error["message"])
            if payload.get("message"):
                return str(payload["message"])
    except (ValueError, requests.RequestException):
        pass

    return response.text.strip() or response.reason or "The Groq API rejected the request."


def load_models(api_key: str) -> Tuple[List[str], str]:
    """Return chat-capable models visible to this specific API key."""
    try:
        response = requests.get(
            f"{GROQ_BASE_URL}/models",
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            timeout=20,
        )
    except requests.RequestException as exc:
        return [], f"Could not connect to Groq: {exc}"

    if not response.ok:
        return [], f"Groq could not load models ({response.status_code}): {api_error(response)}"

    try:
        payload = response.json()
    except ValueError:
        return [], "Groq returned an invalid models response."

    excluded_words = (
        "whisper",
        "guard",
        "safeguard",
        "tts",
        "speech",
        "audio",
        "embedding",
        "moderation",
    )
    models = sorted(
        {
            item.get("id")
            for item in payload.get("data", [])
            if item.get("id")
            and not any(word in item["id"].lower() for word in excluded_words)
        }
    )

    if not models:
        return [], "No chat-capable models were returned for this API key."

    return models, ""


def complete_chat(
    api_key: str,
    model: str,
    messages: List[Dict[str, str]],
) -> str:
    try:
        response = requests.post(
            f"{GROQ_BASE_URL}/chat/completions",
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            json={
                "model": model,
                "messages": messages,
                "max_tokens": 1024,
                "temperature": 0.7,
            },
            timeout=45,
        )
    except requests.Timeout as exc:
        raise RuntimeError(
            "Groq took too long to respond. Try again.") from exc
    except requests.RequestException as exc:
        raise RuntimeError(f"Connection to Groq failed: {exc}") from exc

    if not response.ok:
        detail = api_error(response)
        if response.status_code == 401:
            raise RuntimeError(f"Invalid Groq API key: {detail}")
        if response.status_code == 404:
            raise RuntimeError(
                f"This model is not available for your Groq API key: {detail}"
            )
        if response.status_code == 429:
            raise RuntimeError(f"Groq rate limit reached: {detail}")
        raise RuntimeError(
            f"Groq request failed ({response.status_code}): {detail}")

    try:
        payload = response.json()
        reply = payload["choices"][0]["message"]["content"]
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        raise RuntimeError("Groq returned an unexpected response.") from exc

    if not reply or not str(reply).strip():
        raise RuntimeError("Groq returned an empty response.")

    return str(reply).strip()


def create_new_chat() -> None:
    number = 1
    while f"New chat {number}" in st.session_state.sessions:
        number += 1
    name = f"New chat {number}"
    st.session_state.sessions[name] = []
    st.session_state.active_session = name
    st.session_state.draft = ""


def rename_first_message(session_name: str, message: str) -> None:
    if session_name.startswith("New chat"):
        new_name = message[:28] + ("…" if len(message) > 28 else "")
        if new_name and new_name not in st.session_state.sessions:
            messages = st.session_state.sessions.pop(session_name)
            st.session_state.sessions[new_name] = messages
            st.session_state.active_session = new_name


def export_text(messages: List[Dict[str, str]]) -> str:
    return "\n\n".join(
        f"[{item['role'].upper()}]\n{item['content']}" for item in messages
    )


def render_sidebar(api_key: str) -> Tuple[str, str]:
    with st.sidebar:
        st.title("AI Workspace")

        if st.button("+ New chat", use_container_width=True):
            create_new_chat()
            st.rerun()

        st.subheader("Sessions")
        session_names = list(st.session_state.sessions.keys())
        current_index = session_names.index(st.session_state.active_session)
        active = st.radio(
            "Choose a session",
            session_names,
            index=current_index,
            label_visibility="collapsed",
        )
        if active != st.session_state.active_session:
            st.session_state.active_session = active
            st.rerun()

        st.subheader("Groq API key")
        api_key = st.text_input(
            "API key",
            value=api_key,
            type="password",
            placeholder="gsk_...",
            label_visibility="collapsed",
            help="Use a Groq API key. It is kept only in this browser session.",
        )

        if api_key and api_key != st.session_state.models_key:
            with st.spinner("Loading models available to this key..."):
                models, error = load_models(api_key)
            st.session_state.models = models
            st.session_state.models_key = api_key
            st.session_state.model_error = error

        st.subheader("Chat model")
        if st.session_state.models:
            selected_model = st.selectbox(
                "Model",
                st.session_state.models,
                label_visibility="collapsed",
            )
        else:
            selected_model = st.selectbox(
                "Model",
                DEFAULT_MODELS,
                label_visibility="collapsed",
            )
            if api_key:
                st.warning(
                    st.session_state.model_error or "No models are available.")
            else:
                st.info("Enter your Groq API key to load available models.")

        st.subheader("System prompt")
        st.text_area(
            "System prompt",
            key="system_prompt",
            placeholder="e.g. You are a professional software engineer.",
            label_visibility="collapsed",
        )

        st.subheader("Templates")
        template_columns = st.columns(2)
        for index, (name, prompt) in enumerate(TEMPLATES.items()):
            with template_columns[index % 2]:
                if st.button(name, key=f"template_{name}", use_container_width=True):
                    st.session_state.draft = prompt
                    st.rerun()

        messages = st.session_state.sessions[st.session_state.active_session]
        if messages:
            st.download_button(
                "Export chat",
                data=export_text(messages),
                file_name="ai-workspace-chat.txt",
                mime="text/plain",
                use_container_width=True,
            )

        if st.button("Clear current chat", use_container_width=True):
            st.session_state.sessions[st.session_state.active_session] = []
            st.rerun()

    return selected_model, api_key


def main() -> None:
    st.set_page_config(page_title="AI Workspace", page_icon="🤖", layout="wide")
    initialise_state()

    env_api_key = os.getenv("GROQ_API_KEY", "")
    model, api_key = render_sidebar(env_api_key)
    active_name = st.session_state.active_session
    messages = st.session_state.sessions[active_name]

    st.title(active_name)
    st.caption(f"Model: {model}")

    if not messages:
        st.info("Start a conversation, or choose a template from the sidebar.")

    for message in messages:
        role = message["role"]
        with st.chat_message("assistant" if role == "assistant" else "user"):
            if message.get("error"):
                st.error(message["content"])
            elif role == "assistant":
                st.markdown(message["content"])
            else:
                st.write(message["content"])

    st.divider()
    prompt = st.text_area(
        "Message",
        key="draft",
        placeholder="Ask anything...",
        height=120,
    )
    send_clicked = st.button("Send", type="primary")

    if not send_clicked:
        return

    prompt = prompt.strip()
    if not prompt:
        st.warning("Type a message before sending.")
        return

    if not api_key:
        st.error("Enter your Groq API key in the sidebar first.")
        return

    if not st.session_state.models:
        st.error("No accessible chat models were found for this Groq API key.")
        return

    messages.append({"role": "user", "content": prompt})
    rename_first_message(active_name, prompt)
    active_name = st.session_state.active_session
    messages = st.session_state.sessions[active_name]

    request_messages = [
        {"role": item["role"], "content": item["content"]}
        for item in messages
        if not item.get("error")
    ]
    system_prompt = st.session_state.get("system_prompt", "").strip()
    if system_prompt:
        request_messages.insert(
            0, {"role": "system", "content": system_prompt})

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                reply = complete_chat(api_key, model, request_messages)
                st.markdown(reply)
                messages.append({"role": "assistant", "content": reply})
            except RuntimeError as exc:
                error_message = str(exc)
                st.error(error_message)
                messages.append(
                    {
                        "role": "assistant",
                        "content": error_message,
                        "error": True,
                    }
                )

    st.session_state.clear_draft = True
    st.rerun()


if __name__ == "__main__":
    main()
