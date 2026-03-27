from langgraph.graph import StateGraph, START, END
from langchain.chat_models import init_chat_model
from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages
from src.rag.embedding import get_store
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from src.prompts import AGENT_PROMPT
import os
load_dotenv()


llm = init_chat_model(os.environ.get("CHAT_MODEL"))

vector_store = get_store("files")


class State(TypedDict):
    messages: Annotated[list, add_messages]
    context: str | None
    sources: list[dict] | None


def retriever(state: State):
    """Fetches context from document store based on query"""
    last_message = state["messages"][-1]

    retrieved_docs = vector_store.similarity_search(last_message.content, k=15)

    sources = []
    context_chunks = []

    for i, doc in enumerate(retrieved_docs):
        source_id = f"doc-{i + 1}"
        sources.append({"id": source_id, "name": doc.metadata.get("name", source_id)})

        context_chunks.append(f"[{source_id}] {doc.page_content}")

    return {"context": "\n\n".join(context_chunks), "sources": sources}


def agent_answer(state: State):
    messages = state["messages"]
    context = state.get("context", "")

    messages = [
        SystemMessage(content=f"{AGENT_PROMPT}\n\nKontext:\n{context}")
    ] + messages

    reply = llm.invoke(messages)

    return {
        "messages": [
            AIMessage(
                content=reply.content,
                additional_kwargs={"sources": state.get("sources", [])}
            )
        ]
    }


graph_builder = StateGraph(State)
graph_builder.add_node("retriever", retriever)
graph_builder.add_node("agent", agent_answer)

graph_builder.add_edge(START, "retriever")
graph_builder.add_edge("retriever", "agent")
graph_builder.add_edge("agent", END)

graph = graph_builder.compile()
