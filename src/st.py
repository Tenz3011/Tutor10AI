import streamlit as st
import requests
import os
import json
import re

BASE_URL = "http://localhost:8000"

CHAT="graph"

CHAT_ENDPOINT=f"{BASE_URL}/{CHAT}_chat"

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
    st.set_page_config(page_title="Tutor10AI", page_icon="🎓", initial_sidebar_state="collapsed")

    st.title("🎓 Tutor10AI")
    st.write("Stelle Fragen zu deinen Vorlesungsfolien.")


    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display full conversation
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(convert_latex_delimiters(msg["content"]))

    if "submitted" not in st.session_state:
        st.session_state.submitted = False
    # Input
    user_input = st.chat_input("Deine Frage...")

    if user_input:
        st.session_state.submitted = True
        # Show user message
        st.chat_message("user").markdown(convert_latex_delimiters(user_input))

        st.session_state.messages.append({
            "role": "user",
            "content": user_input
        })


        
        # ============= agent_chat =============
        if CHAT=="agent":
            response = requests.post(
                CHAT_ENDPOINT,
                json={"query": user_input}
            )

            assistant_reply = response.json()["response"]["messages"][-1]["content"][0]["text"]
        
            file_name = "./agent_output.json"

            with open(file_name, "w", encoding="utf-8") as f:
                json.dump(response.json(), f, ensure_ascii=False, indent=2)

        # ============= graph_chat =============

        elif CHAT=="graph":
            response = requests.post(
                CHAT_ENDPOINT,
                json={"messages": st.session_state.messages[-10:]}
            )
            data = response.json() 
            assistant_reply = data["response"]
            sources = data.get("sources", [])



        st.session_state.submitted = False 
        # Show assistant reply
        with st.chat_message("assistant"):
            st.markdown(convert_latex_delimiters(assistant_reply))
    
            if sources:
                with st.expander("📄 Sources"):
                    for src in sources:
                        st.write(f"- **{src['file_name']}** (Seite {src['page']})")

        st.session_state.messages.append({
            "role": "assistant",
            "content": assistant_reply
        })

    with st.sidebar:
        st.header("⚙️ Settings")
        
        if "file_manager" not in st.session_state:
            st.session_state.file_manager = False
        if st.button("📂 Files"):
            st.session_state.file_manager = not st.session_state.file_manager

        if st.session_state.file_manager:
            file = st.file_uploader(
                "Upload PDF",
            )
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
                selected_file = st.selectbox("📄 Select PDF", all_files)
                if st.button("❌ Delete"):
                    delete_file(selected_file)
                    st.warning(f"{selected_file} deleted!")
                    st.rerun()
            else:
                st.info("No files")

                
        st.divider()


        if st.button("📥 Embedding"):
            with st.spinner("downloading..."):
                requests.post(f"{BASE_URL}/embed")

            st.success("✅ files downloaded")
            
# ========================
# HELPERS
# ========================
def extract_text(response):
    messages = response.get("messages", [])

    # iterate from the end to find the last AI message with text
    for msg in reversed(messages):
        if hasattr(msg, "content"):
            content = msg.content

            if isinstance(content, list):
                texts = [
                    part.get("text", "")
                    for part in content
                    if isinstance(part, dict) and part.get("type") == "text"
                ]
                if texts:
                    return " ".join(texts)

            elif isinstance(content, str):
                return content
        

def convert_latex_delimiters(text: str) -> str:
    text = re.sub(r'\\\[(.+?)\\\]', r'$$\1$$', text, flags=re.DOTALL)
    text = re.sub(r'\\\((.+?)\\\)', r'$\1$', text, flags=re.DOTALL)
    return text