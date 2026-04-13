# pip install -qU deepagents
from dotenv import load_dotenv
from deepagents import create_deep_agent

load_dotenv()

def get_weather(city: str) -> str:
    """Get weather for a given city."""
    return f"It's always sunny in {city}!"

agent = create_deep_agent(
    model="openai:gpt-4o-mini",
    tools=[get_weather],
    system_prompt="You are a helpful assistant",
)

# Run the agent
# result = agent.invoke(
#     {"messages": [{"role": "user", "content": "what is the weather in sf"}]}
# )

# print(result["messages"][-1].content[0]["text"])

while True:
    user_input = input("You: ")
    
    if user_input.lower() in ["exit", "quit"]:
        print("Goodbye 👋")
        break

    result = agent.invoke({"messages": [user_input]})

    # Extract assistant reply
    reply = result["messages"][-1].content[0]["text"]

    print(f"Agent: {reply}\n")
