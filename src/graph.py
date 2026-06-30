from typing import TypedDict, Annotated
import os

from dotenv import load_dotenv

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

from langchain.chat_models import init_chat_model
from langchain_core.messages import (
    SystemMessage,
    AIMessage,
)

from src.rag.embedding import get_store
from src.prompts import (
    GRAPH_PROMPT,
    NO_CONTEXT_PROMPT,
    QUIZ_PROMPT
)

load_dotenv()

llm = init_chat_model(os.environ.get("CHAT_MODEL"))
vector_store = get_store("files")

SIMILARITY_THRESHOLD = 0.45


class State(TypedDict):
    messages: Annotated[list, add_messages]
    context: str | None
    sources: list[dict] | None
    mode: str | None


def retriever(state: State):
    """Fetches context from document store based on query"""

    last_message = state["messages"][-1]

    retrieved_docs = vector_store.similarity_search_with_score(
        last_message.content,
        k=10,
    )

    sources = []
    context_chunks = []

    for i, (doc, score) in enumerate(retrieved_docs):

        print(score, doc.metadata)

        if score <= SIMILARITY_THRESHOLD:

            source_id = f"doc-{i+1}"

            metadata = doc.metadata

            sources.append(
                {
                    "id": source_id,
                    "file_name": metadata["file_name"],
                    "page": metadata["page"],
                    "stem": metadata["stem"],
                }
            )

            context_chunks.append(
                f"""
[{source_id}]
File: {metadata['file_name']}
Page: {metadata['page']}

{doc.page_content}
""".strip()
            )

    return {
        "context": "\n\n".join(context_chunks),
        "sources": sources,
    }


def intent_router(state: State):
    """
    Erkennt, ob der Benutzer ein Quiz möchte.
    """

    user_message = state["messages"][-1].content.lower()

    quiz_keywords = [
        "quiz",
        "fragen",
        "fragebogen",
        "test",
        "multiple choice",
        "lernfragen",
    ]

    if any(keyword in user_message for keyword in quiz_keywords):
        return {"mode": "quiz"}

    return {"mode": "chat"}


def router(state: State):

    if not state.get("context"):
        return "no_context"

    if state.get("mode") == "quiz":
        return "quiz"

    return "agent"


def no_context(state: State):

    messages = [
        SystemMessage(content=NO_CONTEXT_PROMPT),
    ]

    reply = llm.invoke(messages)

    return {
        "messages": [
            AIMessage(
                content=reply.content,
                additional_kwargs={
                    "sources": [],
                },
            )
        ]
    }


def agent_answer(state: State):

    messages = state["messages"]
    context = state.get("context")

    prompt = [
        SystemMessage(
            content=f"{GRAPH_PROMPT}\n\nContext:\n{context}"
        )
    ] + messages

    reply = llm.invoke(prompt)

    return {
        "messages": [
            AIMessage(
                content=reply.content,
                additional_kwargs={
                    "sources": state.get("sources", []),
                },
            )
        ]
    }


def quiz_generator(state: State):
    """
    Erstellt ein Quiz anhand der gefundenen Dokumente.
    """

    context = state.get("context")

    messages = [
        SystemMessage(
            content=f"{QUIZ_PROMPT}\n\nKontext:\n{context}"
        )
    ]

    reply = llm.invoke(messages)

    return {
        "messages": [
            AIMessage(
                content=reply.content,
                additional_kwargs={
                    "sources": state.get("sources", []),
                },
            )
        ]
    }


graph_builder = StateGraph(State)

graph_builder.add_node("retriever", retriever)
graph_builder.add_node("intent", intent_router)
graph_builder.add_node("agent", agent_answer)
graph_builder.add_node("quiz", quiz_generator)
graph_builder.add_node("no_context", no_context)

graph_builder.add_edge(START, "retriever")
graph_builder.add_edge("retriever", "intent")

graph_builder.add_conditional_edges(
    "intent",
    router,
    {
        "agent": "agent",
        "quiz": "quiz",
        "no_context": "no_context",
    },
)

graph_builder.add_edge("agent", END)
graph_builder.add_edge("quiz", END)
graph_builder.add_edge("no_context", END)

graph = graph_builder.compile()