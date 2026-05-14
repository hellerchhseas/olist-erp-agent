"""
agent.py

This file runs the interactive command-line version of the ERP Operations Agent.

Use this when you want to chat with the agent manually.

Example:

    python agent.py

Then type:

    Find 3 late shipments delayed by more than 10 days.

This file intentionally stays small because the reusable setup code lives in
agent_factory.py.
"""

import asyncio

from agent_factory import (
    create_erp_agent,
    is_debug_trace_enabled,
    print_debug_trace,
)


async def main() -> None:
    """
    Start the interactive ERP Operations Agent.

    High-level flow:
    1. Check whether debug trace mode is enabled.
    2. Create the agent and load MCP tools.
    3. Print available tools.
    4. Start a terminal chat loop.
    5. Send each user message to the agent.
    6. Print the agent's answer.
    7. Optionally print the debug trace.
    """
    # Read DEBUG_TRACE from .env.
    # If DEBUG_TRACE=true, the program will print tool calls and tool results.
    debug_trace = is_debug_trace_enabled()

    # Create the agent and load tools from the MCP server.
    #
    # create_erp_agent() is defined in agent_factory.py.
    # It handles:
    # - loading the prompt
    # - creating the OpenAI model
    # - connecting to the MCP server
    # - loading MCP tools
    # - creating the LangChain agent
    agent, tools = await create_erp_agent()

    # Print the tools so we can confirm the MCP server connection worked.
    print("\nLoaded MCP tools:")
    for tool in tools:
        print(f"- {tool.name}")

    print("\nERP Operations Agent")
    print("Type a question. Type 'exit' or 'quit' to stop.")

    if debug_trace:
        print("Debug trace: ON")
    else:
        print("Debug trace: OFF")

    print()

    # Main command-line loop.
    #
    # This loop keeps running until the user types "exit" or "quit".
    while True:
        # Read input from the terminal.
        user_input = input("You: ").strip()

        # Allow the user to exit cleanly.
        if user_input.lower() in {"exit", "quit"}:
            break

        # Send the user's message to the agent.
        #
        # The agent may:
        # - answer directly
        # - call one or more MCP tools
        # - inspect tool results
        # - create notes/tasks
        # - produce a final answer
        result = await agent.ainvoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": user_input,
                    }
                ]
            }
        )

        # The final message is normally the assistant's final response.
        final_message = result["messages"][-1]

        print("\nAgent:")
        print(final_message.content)
        print()

        # If debug mode is enabled, print the tool-call trace.
        if debug_trace:
            print_debug_trace(result)


# Python only runs this block when the file is executed directly:
#
#     python agent.py
#
# It does not run this block when another file imports agent.py.
if __name__ == "__main__":
    asyncio.run(main())