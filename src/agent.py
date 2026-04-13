from src.rag.embedding import get_store
from dotenv import load_dotenv
from deepagents import create_deep_agent
from src.prompts import AGENT_PROMPT

load_dotenv()
vector_store = get_store("files")

def retrieve_context(query: str):
    """Retrieve relevant documents for a query. Returns context with sources."""
    retrieved_docs = vector_store.similarity_search(query, k=5)

    sources = []
    chunks = []

    for i, doc in enumerate(retrieved_docs):
        source_id = f"doc-{i+1}"
        name = doc.metadata.get("name", source_id)

        sources.append({"id": source_id, "name": name})
        chunks.append(f"[{source_id}] {doc.page_content}")

    return "\n\n".join(chunks)


agent = create_deep_agent(
    model="openai:gpt-4o-mini",
    tools=[retrieve_context],
    system_prompt=AGENT_PROMPT,
)