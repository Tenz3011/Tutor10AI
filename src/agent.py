from src.rag.embedding import get_store
from dotenv import load_dotenv
from deepagents import create_deep_agent
from src.prompts import AGENT_PROMPT
import requests
import os
import time
from bs4 import BeautifulSoup

load_dotenv()


vector_store = get_store("files")

# ---------------- TOOLS ---------------- 

def retrieve_context(query: str) -> str:
    """
    Retrieve internal documents. Use for company/private knowledge.
    """
    retrieved_docs = vector_store.similarity_search(query, k=5)

    chunks = []
    for i, doc in enumerate(retrieved_docs):
        source_id = f"doc-{i+1}"

        metadata = "\n".join(
            f"{k}: {v}" for k, v in doc.metadata.items()
        )

        chunks.append(
            f"""
[{source_id}]
METADATA:
{metadata}

CONTENT:
{doc.page_content}
""".strip()
        )

    return "\n\n".join(chunks)



def websearch(query: str) -> str:
    """
    Use for current events or unknown external info.
    """
    api_key = os.getenv("LANGSEARCH_API_KEY")

    response = requests.post(
        "https://api.langsearch.com/v1/web-search",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        json={
            "query": query,
            "freshness": "noLimit",
            "summary": True,
            "count": 1,
        }
    )

    data = response.json()
    results = data["data"]["webPages"]["value"]
    return results[0].get("snippet", "")

HEADERS = {
    "User-Agent": "MySearchBot/1.0 (contact: your_email@example.com)"
}

def serper_websearch(query: str) -> str:
    """
    General web search tool:
    - uses Serper for search
    - fetches page content safely
    - returns cleaned text
    """
    api_key = os.getenv("SERPER_API_KEY")

    # Step 1: Search
    search_res = requests.post(
        "https://google.serper.dev/search",
        headers={
            "X-API-KEY": api_key,
            "Content-Type": "application/json"
        },
        json={"q": query, "num": 3}
    ).json()

    results = search_res.get("organic", [])
    if not results:
        return "No results found."

    url = results[0].get("link")

    # Step 2: Fetch page (with User-Agent)
    try:
        time.sleep(1)  # basic politeness delay
        page = requests.get(url, headers=HEADERS, timeout=10)
        page.raise_for_status()
    except Exception as e:
        return f"Failed to fetch page: {e}"

    # Step 3: Parse HTML
    soup = BeautifulSoup(page.text, "html.parser")

    # Remove junk
    for tag in soup(["script", "style", "noscript", "header", "footer", "nav"]):
        tag.extract()

    # Try to focus on main content
    main = soup.find("main") or soup.find("article") or soup.body

    text = main.get_text(separator=" ") if main else soup.get_text(separator="\n")

    # Clean text
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    content = "\n".join(lines)

    return content[:4000]
# ---------------- SUBAGENTS ---------------- #

subagents = [
    {
        "name": "rag-agent",
        "description": "Retrieves relevant internal knowledge chunks",
        "system_prompt": """
You are a retrieval agent.

Your job:
- Retrieve relevant information using the tool
- Return ONLY extracted facts
- DO NOT write reports
- DO NOT summarize broadly
- Keep output grounded in retrieved content

Format:
[doc-1] ...
[doc-2] ...
""",
        "tools": [retrieve_context],
        "model": "openai:gpt-4o-mini",
    },
    {
        "name": "web-agent",
        "description": "Fetches external information from the web",
        "system_prompt": """
You are a web extraction agent.

Your job:
- Use web search
- Extract relevant factual information
- DO NOT write reports
- DO NOT add prior knowledge

Output format:
[SOURCE: url]
- fact 1
- fact 2
""",
        "tools": [serper_websearch],
        "model": "openai:gpt-4o-mini",
    },
    {
    "name": "analysis-agent",
    "description": "Synthesizes information into structured insights",
    "system_prompt": """
You are an analysis agent.

Your job:
- Combine inputs from other agents
- Identify patterns, trends, and key insights
- Resolve conflicting information if possible
- Stay grounded in provided evidence

Output:
- Key insights
- Supporting evidence references
- Clear reasoning
""",
    "tools": [],
    "model": "openai:gpt-4o-mini",
}
]

# ---------------- MAIN AGENT ---------------- #

agent = create_deep_agent(
    model="openai:gpt-4o-mini",
    # tools=[retrieve_context, websearch],  # still required
    system_prompt=AGENT_PROMPT,
    subagents=subagents,    # type: ignore
    skills=["/skills/decomposeaggregate/"]

)