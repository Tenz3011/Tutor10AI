from fastapi import FastAPI
from src.rag.embedding import embed
from pydantic import BaseModel
from src.graph import graph
from langchain_core.messages import HumanMessage, AIMessage
import asyncio

app = FastAPI()

class ChatRequest(BaseModel):
    messages: list[dict]


@app.post("/embed")
async def embedding():
    await asyncio.to_thread(embed)
    return {"status": "ok"}

def to_lc_messages(messages):

    lc = []
    for msg in messages:
        if msg["role"] == "user":
            lc.append(HumanMessage(content=msg["content"]))
        else:
            lc.append(AIMessage(content=msg["content"]))
    return lc

@app.post("/chat")
async def chat(req: ChatRequest):
    messages = req.messages
    lc_messages = to_lc_messages(messages)
    print(lc_messages)
    state = {"messages": lc_messages}
    print(state)

    result = await asyncio.to_thread(graph.invoke, state) # type: ignore
    assistant_reply = result["messages"][-1].content
    print(f"REPLY: {assistant_reply}")

    return {"response": assistant_reply}

