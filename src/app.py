import streamlit as st
from langchain_core.messages import HumanMessage
from graph import graph  
from embedding import embed

def app():
    st.set_page_config(page_title="Tutor10AI", page_icon="🎓")

    st.title("🎓 Tutor10AI")
    st.write("Stelle Fragen zu deinen Vorlesungsfolien.")

    # Chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat history
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

        # Call your graph
        state = {
            "messages": [HumanMessage(content=user_input)]
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

        if st.button("📥 Embedding"):
            with st.spinner("Embedding läuft..."):
                embed()

            st.success("✅ Erfolgreich eingebettet!")