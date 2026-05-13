import asyncio
import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.messages import AIMessage, ToolMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI


# ------------------------------------------------------------
# Load environment variables from .env
# ------------------------------------------------------------
# This repo's .env should contain:
#
# OPENAI_API_KEY=your_openai_api_key_here
# DEBUG_TRACE=true
#
# Supabase credentials live in the MCP repo's .env because the MCP
# server is the component that talks directly to Supabase.
load_dotenv()


# ------------------------------------------------------------
# Local MCP server configuration
# ------------------------------------------------------------
# This agent launches the Olist ERP MCP server as a subprocess.
#
# MCP repo:
#   ~/dev/olist-erp-mcp
#
# Agent repo:
#   ~/dev/olist-erp-agent
#
# The agent does not import the MCP tools directly. It connects to the
# MCP server and receives the tools through the MCP protocol.
MCP_WORKING_DIR = "/Users/christianheller/dev/olist-erp-mcp"
MCP_PYTHON_PATH = "/Users/christianheller/dev/olist-erp-mcp/.venv/bin/python"


def load_system_prompt() -> str:
    """
    Load the ERP Operations Agent system prompt from a markdown file.

    Keeping the prompt separate makes it easier to edit behavior without
    modifying Python code.
    """
    return Path("prompts/erp_operations_agent.md").read_text()


def is_debug_trace_enabled() -> bool:
    """
    Read DEBUG_TRACE from the .env file.

    Accepted true values:
    - true
    - 1
    - yes
    - y

    Anything else is treated as false.
    """
    return os.getenv("DEBUG_TRACE", "false").lower() in {"true", "1", "yes", "y"}


def compact_json(value: Any, max_chars: int = 900) -> str:
    """
    Convert a Python object into readable, truncated JSON text.

    This keeps tool trace output useful without flooding the terminal
    with huge JSON responses.
    """
    try:
        text = json.dumps(value, indent=2, default=str, ensure_ascii=False)
    except TypeError:
        text = str(value)

    if len(text) > max_chars:
        return text[:max_chars] + "\n... [truncated]"
    return text


def print_debug_trace(result: dict[str, Any]) -> None:
    """
    Print a readable trace of model tool calls and tool results.

    LangChain agent results include a list of messages:
    - Human/user messages
    - AI messages
    - Tool messages
    - Final assistant message

    AI messages may contain tool_calls.
    Tool messages contain the result returned by each tool.

    This function walks through those messages and prints:
    - which tools were called
    - what arguments were passed
    - a short preview of each tool result
    """
    messages = result.get("messages", [])

    tool_call_count = 0
    tool_result_count = 0

    print("\n--- DEBUG TRACE ---")

    for message in messages:
        # AIMessage objects may include a .tool_calls list.
        if isinstance(message, AIMessage):
            tool_calls = getattr(message, "tool_calls", None) or []

            for tool_call in tool_calls:
                tool_call_count += 1

                tool_name = tool_call.get("name", "unknown_tool")
                tool_args = tool_call.get("args", {})

                print(f"\nTool call {tool_call_count}: {tool_name}")
                print("Arguments:")
                print(compact_json(tool_args, max_chars=700))

        # ToolMessage objects contain tool execution results.
        elif isinstance(message, ToolMessage):
            tool_result_count += 1

            tool_name = getattr(message, "name", None) or "unknown_tool"
            content = getattr(message, "content", "")

            print(f"\nTool result {tool_result_count}: {tool_name}")
            print("Result preview:")
            print(str(content)[:900] + ("...\n[truncated]" if len(str(content)) > 900 else ""))

    if tool_call_count == 0 and tool_result_count == 0:
        print("No tool calls were recorded for this turn.")

    print("--- END DEBUG TRACE ---\n")


async def main() -> None:
    """
    Main async entrypoint for the ERP Operations Agent.

    High-level flow:
    1. Load the system prompt.
    2. Create the OpenAI chat model.
    3. Launch/connect to the local MCP server.
    4. Load MCP tools as LangChain-compatible tools.
    5. Create a LangChain/LangGraph agent using those tools.
    6. Start a command-line chat loop.
    7. Optionally print a debug trace after each agent response.
    """

    # ------------------------------------------------------------
    # 1. Load the system prompt
    # ------------------------------------------------------------
    system_prompt = load_system_prompt()

    # ------------------------------------------------------------
    # 2. Read debug configuration
    # ------------------------------------------------------------
    debug_trace = is_debug_trace_enabled()

    # ------------------------------------------------------------
    # 3. Create the LLM
    # ------------------------------------------------------------
    # temperature=0 makes the model more deterministic, which is better
    # for operational workflows involving tools and record inspection.
    model = ChatOpenAI(
        model="gpt-4.1-mini",
        temperature=0,
    )

    # ------------------------------------------------------------
    # 4. Configure MCP client
    # ------------------------------------------------------------
    # MultiServerMCPClient can connect to one or more MCP servers.
    #
    # Here we configure one server named "olist_erp".
    #
    # The MCP subprocess is launched with:
    # - the MCP repo's Python executable
    # - the MCP server module
    # - the MCP repo as its working directory
    # - PYTHONPATH=. so Python can import src.olist_erp_mcp
    client = MultiServerMCPClient(
        {
            "olist_erp": {
                "command": MCP_PYTHON_PATH,
                "args": ["-m", "src.olist_erp_mcp.server"],
                "transport": "stdio",
                "cwd": MCP_WORKING_DIR,
                "env": {
                    "PYTHONPATH": ".",
                },
            }
        }
    )

    # ------------------------------------------------------------
    # 5. Load MCP tools
    # ------------------------------------------------------------
    # This asks the MCP server what tools it exposes, then converts them
    # into LangChain-compatible tools.
    tools = await client.get_tools()

    print("\nLoaded MCP tools:")
    for tool in tools:
        print(f"- {tool.name}")

    # ------------------------------------------------------------
    # 6. Create the agent
    # ------------------------------------------------------------
    agent = create_agent(
        model=model,
        tools=tools,
        system_prompt=system_prompt,
    )

    # ------------------------------------------------------------
    # 7. Start CLI loop
    # ------------------------------------------------------------
    print("\nERP Operations Agent")
    print("Type a question. Type 'exit' or 'quit' to stop.")

    if debug_trace:
        print("Debug trace: ON")
    else:
        print("Debug trace: OFF")

    print()

    while True:
        user_input = input("You: ").strip()

        if user_input.lower() in {"exit", "quit"}:
            break

        # --------------------------------------------------------
        # Invoke the agent
        # --------------------------------------------------------
        # The agent may:
        # - inspect the user request
        # - call one or more MCP tools
        # - observe tool results
        # - call additional tools
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

        # --------------------------------------------------------
        # Print final response
        # --------------------------------------------------------
        final_message = result["messages"][-1]

        print("\nAgent:")
        print(final_message.content)
        print()

        # --------------------------------------------------------
        # Optional debug trace
        # --------------------------------------------------------
        # This prints the tool calls and tool results for the turn.
        # Useful for development and demos.
        if debug_trace:
            print_debug_trace(result)


if __name__ == "__main__":
    asyncio.run(main())