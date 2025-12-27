import asyncio
from langchain_core.messages import SystemMessage, HumanMessage
from agent.graph import graph


async def main():
    with open("agent/system_prompt.jinja", "r") as f:
        system_prompt = f.read()

    state = {
        "messages": [
            SystemMessage(
                content=system_prompt
            )
        ],
        "current_position": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    }

    while True:
        # read and append user message"
        new_message = input("User: ")
        state["messages"].append(HumanMessage(content=new_message))

        # receive new state
        state = await graph.ainvoke(state)
        assistant_message = state["messages"][-1].content
        print(f"Assistant: {assistant_message}")




if __name__ == "__main__":
    asyncio.run(main())
