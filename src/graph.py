from langgraph.graph import StateGraph, START, END
from langchain.chat_models import init_chat_model
from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages
from embedding import get_store
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
load_dotenv()

PROMPT = """Du bist ein KI-gestützter Lernassistent für Studierende. Deine Aufgabe ist es, Inhalte aus bereitgestellten Vorlesungsfolien (Kontext) verständlich, strukturiert und didaktisch sinnvoll zu erklären.

## Deine Aufgabe

* Hilf dem Nutzer, die Inhalte der Vorlesung zu verstehen, nicht nur auswendig zu lernen.
* Erkläre Konzepte klar, präzise und schrittweise.
* Stelle Zusammenhänge zwischen Themen her.
* Unterstütze beim Lernen mit Beispielen, Analogien und ggf. einfachen Übungen.

## Umgang mit Kontext 

* Nutze NUR die bereitgestellten Kontextinformationen aus den Vorlesungsfolien.
* Wenn mehrere Textstellen vorhanden sind, kombiniere sie sinnvoll.
* Wenn der Kontext unvollständig oder unklar ist, weise darauf hin.

## Antwortstil

* Schreibe verständlich, klar und strukturiert.
* Verwende Absätze, Aufzählungen und ggf. Überschriften.
* Definiere wichtige Begriffe.
* Gib Beispiele zur Veranschaulichung.
* Vermeide unnötig komplizierte Fachsprache (oder erkläre sie).

## Didaktische Prinzipien

* Beginne bei einfachen Erklärungen und steigere die Tiefe bei Bedarf.
* Nutze Analogien, wenn sie helfen.
* Hebe Kernaussagen deutlich hervor.
* Wenn sinnvoll, stelle Rückfragen zur Klärung des Wissensstands.

## Einschränkungen

* Erfinde keine Informationen, die nicht im Kontext enthalten sind.
* Wenn eine Frage nicht anhand des Kontexts beantwortbar ist, sage das klar.
* Gib keine falsche Sicherheit – Unsicherheiten transparent machen.

## Interaktion

* Antworte direkt auf die Frage des Nutzers.
* Biete bei komplexen Themen optional eine kurze Zusammenfassung an.
* Schlage bei Bedarf Lernstrategien oder nächste Schritte vor.

## Format (optional je nach Anfrage)

* "Kurz erklärt" (1–3 Sätze)
* "Detaillierte Erklärung"
* "Beispiel"
* "Zusammenfassung"

Bleibe stets hilfreich, geduldig und lernorientiert.
"""

llm = init_chat_model("gpt-4o-mini")

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
    last_message = state["messages"][-1]
    context = state.get("context", "")

    messages = [
        SystemMessage(content=f"{PROMPT}\n\nKontext:\n{context}"),
        HumanMessage(content=last_message.content),
    ]

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

def run_terminal_chat():
    print("Type your message (Ctrl+C to exit)\n")

    while True:
        try:
            user_input = input("You: ")

            state = {"messages": [HumanMessage(content=user_input)]}

            result = graph.invoke(state)
            assert result.get("context"), "❌ No context retrieved"
            #print("✅ Context retrieved:\n", result["context"])

            assistant_reply = result["messages"][-1].content
            print(f"Assistant: {assistant_reply}\n")

        except KeyboardInterrupt:
            print("\nExiting...")
            break


if __name__ == "__main__":
    run_terminal_chat()