from langgraph.graph import StateGraph, START, END
from langchain.chat_models import init_chat_model
from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages
from src.rag.embedding import get_store
from dotenv import load_dotenv
from langchain_core.messages import  SystemMessage, AIMessage
from src.prompts import GRAPH_PROMPT, NO_CONTEXT_PROMPT
import os

load_dotenv()
llm = init_chat_model(os.environ.get("CHAT_MODEL"))
vector_store = get_store("files")

SIMILARITY_THRESHOLD = 0.50

class State(TypedDict):
    messages: Annotated[list, add_messages]
    context: str | None
    sources: list[dict] | None


def retriever(state: State):
    """Fetches context from document store based on query"""
    last_message = state["messages"][-1]

    retrieved_docs = vector_store.similarity_search_with_score(last_message.content, k=10)

    sources = []
    context_chunks = []

    for i, (doc,score) in enumerate(retrieved_docs):
        print(score, doc.metadata)
        if score <= SIMILARITY_THRESHOLD:
            source_id = f"doc-{i+1}"

            metadata = doc.metadata

            sources.append({
                "id": source_id,
                "file_name": metadata["file_name"],
                "page": metadata["page"],
                "stem": metadata["stem"],
            })

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

def router(state: State):
    if state.get("context"):
        return "agent"
    return "no_context"

def no_context(state: State):

    messages = [
        SystemMessage(content=NO_CONTEXT_PROMPT),
    ] 
 
    reply = llm.invoke(messages)
    return {
        "messages": [
            AIMessage(
                content=reply.content,
                additional_kwargs={"sources": []},
            )
        ]
    }
    
def agent_answer(state: State):
    messages = state["messages"]
    context = state.get("context")

    messages = [
        SystemMessage(content=f"{GRAPH_PROMPT}\n\nContext:\n{context}")
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
graph_builder.add_node("no_context", no_context)


graph_builder.add_edge(START, "retriever")
graph_builder.add_conditional_edges(
    "retriever",
    router,
    {
        "agent": "agent",
        "no_context": "no_context",
    },
)
graph_builder.add_edge("no_context", END)
graph_builder.add_edge("agent", END)

graph = graph_builder.compile()
