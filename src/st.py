import os
import re
import requests
import streamlit as st

BASE_URL = "http://localhost:8000"

CHAT = "graph"
CHAT_ENDPOINT = f"{BASE_URL}/{CHAT}_chat"

MAX_MESSAGES = 10
FILE_DIR = "files"
os.makedirs(FILE_DIR, exist_ok=True)


def save_uploaded_file(file):
    path = os.path.join(FILE_DIR, file.name)
    with open(path, "wb") as f:
        f.write(file.read())
    return path


def list_files():
    return sorted([f for f in os.listdir(FILE_DIR) if f.endswith(".pdf")])


def delete_file(filename):
    os.remove(os.path.join(FILE_DIR, filename))


def st_app():
    st.set_page_config(
        page_title="Tutor10AI",
        page_icon="🎓",
        initial_sidebar_state="collapsed",
    )

    st.title("🎓 RAG Tutor")
    st.write("Stelle Fragen zu deinen Vorlesungsfolien oder lasse dir ein Quiz erstellen.")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "mode" not in st.session_state:
        st.session_state.mode = "Chat"

    # -----------------------------
    # Sidebar
    # -----------------------------
    with st.sidebar:

        st.header("⚙️ Settings")

        st.subheader("Modes")
        st.session_state.mode = st.radio(
            "Select a mode",
            ["Chat", "Quiz"],
        )

        st.divider()

        if "file_manager" not in st.session_state:
            st.session_state.file_manager = False

        if st.button("📂 Files"):
            st.session_state.file_manager = (
                not st.session_state.file_manager
            )

        if st.session_state.file_manager:

            file = st.file_uploader("Upload PDF")

            if file:

                path = os.path.join(FILE_DIR, file.name)

                if os.path.exists(path):
                    st.warning("⚠️ File already exists!")

                else:
                    save_uploaded_file(file)
                    st.success(f"{file.name} saved!")
                    st.rerun()

            all_files = list_files()

            if all_files:

                selected_file = st.selectbox(
                    "📄 Select PDF",
                    all_files,
                )

                if st.button("❌ Delete"):
                    delete_file(selected_file)
                    st.warning(f"{selected_file} deleted!")
                    st.rerun()

            else:
                st.info("No files")

        st.divider()

        if st.button("📥 Embedding"):

            with st.spinner("Embedding..."):
                requests.post(f"{BASE_URL}/embed")

            st.success("✅ Files embedded")

    # -----------------------------
    # Chatverlauf anzeigen
    # -----------------------------
    for msg in st.session_state.messages:

        with st.chat_message(msg["role"]):
            st.markdown(convert_latex_delimiters(msg["content"]))

    # -----------------------------
    # Chat Input
    # -----------------------------
    user_input = st.chat_input("Deine Frage...")

    if user_input:

        original_input = user_input

        # Quizmodus
        if st.session_state.mode == "Quiz":
            user_input = (
                "Erstelle ein Quiz ausschließlich anhand der Dokumente "
                f"zum folgenden Thema:\n\n{original_input}"
            )

        st.chat_message("user").markdown(
            convert_latex_delimiters(original_input)
        )

        st.session_state.messages.append(
            {
                "role": "user",
                "content": user_input,
            }
        )

        with st.spinner("Denke nach..."):

            response = requests.post(
                CHAT_ENDPOINT,
                json={
                    "messages": st.session_state.messages[-MAX_MESSAGES:]
                },
            )

        data = response.json()

        assistant_reply = data["response"]
        sources = data.get("sources", [])

        with st.chat_message("assistant"):

            st.markdown(convert_latex_delimiters(assistant_reply))

            if sources:

                with st.expander("📄 Sources"):

                    for src in sources:
                        st.write(
                            f"- **{src['file_name']}** "
                            f"(Seite {src['page']})"
                        )

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": assistant_reply,
            }
        )


# ========================
# Helpers
# ========================

def extract_text(response):
    messages = response.get("messages", [])

    for msg in reversed(messages):

        if hasattr(msg, "content"):

            content = msg.content

            if isinstance(content, list):

                texts = [
                    part.get("text", "")
                    for part in content
                    if isinstance(part, dict)
                    and part.get("type") == "text"
                ]

                if texts:
                    return " ".join(texts)

            elif isinstance(content, str):
                return content


def convert_latex_delimiters(text: str) -> str:
    text = re.sub(r"\\\[(.+?)\\\]", r"$$\1$$", text, flags=re.DOTALL)
    text = re.sub(r"\\\((.+?)\\\)", r"$\1$", text, flags=re.DOTALL)
    return text


if __name__ == "__main__":
    st_app()