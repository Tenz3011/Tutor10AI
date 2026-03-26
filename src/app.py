import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage
from graph import graph  
from embedding import embed
import os

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

def to_lc_messages(): 
    recent_messages = st.session_state.messages[-MAX_MESSAGES:]
    lc = [] 
    for msg in recent_messages: 
        if msg["role"] == "user": 
            lc.append(HumanMessage(content=msg["content"])) 
        else: 
            lc.append(AIMessage(content=msg["content"])) 
    return lc

def app():
    st.set_page_config(page_title="Tutor10AI", page_icon="🎓", initial_sidebar_state="collapsed")

    st.title("🎓 Tutor10AI")
    st.write("Stelle Fragen zu deinen Vorlesungsfolien.")


    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Input
    user_input = st.chat_input("Deine Frage...")

    if user_input:
        # Show user message
        st.chat_message("user").markdown(user_input)

        st.session_state.messages.append({
            "role": "user",
            "content": user_input
        })

        all_messages = to_lc_messages()

        state = {
            "messages": all_messages
        }

        result = graph.invoke(state)

        assistant_reply = result["messages"][-1].content

        # Show assistant reply
        with st.chat_message("assistant"):
            st.markdown(assistant_reply)
    
            # if result.get("sources"):
            #     with st.expander("📚 Quellen"):
            #         for src in result["sources"]:
            #             st.write(f"- {src['name']} ({src['id']})")

        st.session_state.messages.append({
            "role": "assistant",
            "content": assistant_reply
        })

    with st.sidebar:
        st.header("⚙️ Einstellungen")
        
        if "file_manager" not in st.session_state:
            st.session_state.file_manager = False
        if st.button("📂 Files"):
            st.session_state.file_manager = not st.session_state.file_manager

        if st.session_state.file_manager:
            file = st.file_uploader(
                "PDF hochladen",
            )
            if file:
                path = os.path.join(FILE_DIR, file.name)
                if os.path.exists(path):
                    st.warning("⚠️ Datei existiert bereits!")
                else:
                    save_uploaded_file(file)
                    st.success(f"{file.name} gespeichert!")
                    st.rerun()
            
            all_files = list_files()

            if all_files:
                selected_file = st.selectbox("📄 PDFs auswählen", all_files)
                if st.button("❌ Löschen"):
                    delete_file(selected_file)
                    st.warning(f"{selected_file} gelöscht!")
                    st.rerun()
            else:
                st.info("Keine Dateien vorhanden")

                
        st.divider()


        if st.button("📥 Embedding"):
            with st.spinner("Embedding läuft..."):
                embed()

            st.success("✅ Erfolgreich eingebettet!")