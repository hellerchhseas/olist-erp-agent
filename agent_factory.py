"""
agent_factory.py

This file contains the reusable setup code for the ERP Operations Agent.

Why this file exists:
- We do not want to repeat the same setup code in every script.
- The interactive CLI agent and the scripted workflow files all need the same things:
  1. Load environment variables
  2. Create an OpenAI chat model
  3. Connect to the local MCP server
  4. Load MCP tools
  5. Create a LangChain/LangGraph agent
  6. Optionally print debug traces

Think of this file as the "agent construction kit."
"""

import json
import os
import logging
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.messages import AIMessage, ToolMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI


# ------------------------------------------------------------
# Load environment variables
# ------------------------------------------------------------
# load_dotenv() reads values from the local .env file and makes them
# available through os.getenv() or os.environ.
#
# In this repo, .env should contain:
#
# OPENAI_API_KEY=your_openai_api_key_here
# DEBUG_TRACE=true_or_false
#
# This repo does NOT need Supabase credentials.
# Supabase credentials live in the MCP server repo because the MCP server,
# not this agent, talks directly to Supabase.
load_dotenv()

# ------------------------------------------------------------
# Suppress noisy infrastructure logs
# ------------------------------------------------------------
# MCP, HTTPX, and Supabase can print a lot of low-level request logs.
# Those are useful when debugging connectivity, but they make workflow
# demos hard to read.
#
# We set them to WARNING so the terminal focuses on:
# - loaded tools
# - agent summary
# - optional debug trace
logging.getLogger("mcp").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("supabase").setLevel(logging.WARNING)
logging.getLogger("postgrest").setLevel(logging.WARNING)


# ------------------------------------------------------------
# MCP server configuration
# ------------------------------------------------------------
# The agent will launch the MCP server as a subprocess.
#
# The MCP server lives in a separate local repo:
#
#   /Users/christianheller/dev/olist-erp-mcp
#
# That MCP server exposes tools like:
# - list_late_shipments_tool
# - get_order_tool
# - get_invoice_tool
# - create_agent_task_tool
# - add_agent_note_tool
#
# This agent communicates with those tools through the MCP protocol.
MCP_WORKING_DIR = "/Users/christianheller/dev/olist-erp-mcp"

# This is the Python executable inside the MCP repo's virtual environment.
# We use this Python so the MCP server has access to its own installed packages:
# mcp, supabase, python-dotenv, etc.
MCP_PYTHON_PATH = "/Users/christianheller/dev/olist-erp-mcp/.venv/bin/python"


def load_system_prompt() -> str:
    """
    Load the system prompt from a markdown file.

    The system prompt tells the model how to behave.

    In this project, the prompt tells the model:
    - act like an ERP operations analyst
    - use tools before making factual claims
    - create notes/tasks when follow-up is needed
    - avoid inventing data

    We keep the prompt in a separate file because prompts are easier to edit
    as text than as Python strings.
    """
    return Path("prompts/erp_operations_agent.md").read_text()


def is_debug_trace_enabled() -> bool:
    """
    Check whether debug tracing is turned on.

    The value comes from .env:

        DEBUG_TRACE=true

    Accepted true values:
    - true
    - 1
    - yes
    - y

    Anything else is treated as false.

    Why this matters:
    - In normal demo mode, you may only want the final agent answer.
    - In learning/debug mode, you want to see which tools the agent called.
    """
    return os.getenv("DEBUG_TRACE", "false").lower() in {"true", "1", "yes", "y"}


def compact_json(value: Any, max_chars: int = 900) -> str:
    """
    Convert a Python object into readable JSON text.

    Tool results can be large. For example, a shipment record might include
    many fields, and a list of records can become very long.

    This helper:
    - converts objects into formatted JSON
    - truncates the output if it gets too long

    That keeps debug traces useful without flooding the terminal.
    """
    try:
        # json.dumps converts Python objects into JSON-formatted strings.
        # indent=2 makes it easier for humans to read.
        # default=str prevents crashes if an object is not naturally JSON serializable.
        # ensure_ascii=False keeps non-English characters readable.
        text = json.dumps(value, indent=2, default=str, ensure_ascii=False)
    except TypeError:
        # Fallback: if JSON conversion fails, just convert the object to a string.
        text = str(value)

    # If the JSON text is too long, cut it down and add a note.
    if len(text) > max_chars:
        return text[:max_chars] + "\n... [truncated]"

    return text


def print_debug_trace(result: dict[str, Any]) -> None:
    """
    Print a readable trace of the agent's tool calls.

    When LangChain runs an agent, the result contains a message history.

    That history can include:
    - the original user message
    - AI messages where the model decides to call a tool
    - Tool messages containing tool results
    - the final assistant response

    This function walks through those messages and prints:
    - which tools were called
    - what arguments were passed
    - a short preview of each tool result

    Why this is useful:
    - It shows whether the agent actually used tools.
    - It helps you debug bad behavior.
    - It makes demos easier because you can explain the execution path.
    """
    messages = result.get("messages", [])

    tool_call_count = 0
    tool_result_count = 0

    print("\n--- DEBUG TRACE ---")

    for message in messages:
        # AIMessage is a model-generated message.
        # Some AI messages contain tool calls, meaning:
        # "The model decided it needs to call this tool with these arguments."
        if isinstance(message, AIMessage):
            tool_calls = getattr(message, "tool_calls", None) or []

            for tool_call in tool_calls:
                tool_call_count += 1

                # Each tool call usually has:
                # - name: the tool name
                # - args: the input arguments passed to the tool
                tool_name = tool_call.get("name", "unknown_tool")
                tool_args = tool_call.get("args", {})

                print(f"\nTool call {tool_call_count}: {tool_name}")
                print("Arguments:")
                print(compact_json(tool_args, max_chars=700))

        # ToolMessage is the result returned by a tool.
        # Example: list_late_shipments_tool returns rows from Supabase.
        elif isinstance(message, ToolMessage):
            tool_result_count += 1

            tool_name = getattr(message, "name", None) or "unknown_tool"
            content = getattr(message, "content", "")

            print(f"\nTool result {tool_result_count}: {tool_name}")
            print("Result preview:")

            content_text = str(content)

            if len(content_text) > 900:
                print(content_text[:900] + "...\n[truncated]")
            else:
                print(content_text)

    if tool_call_count == 0 and tool_result_count == 0:
        print("No tool calls were recorded for this turn.")

    print("--- END DEBUG TRACE ---\n")


async def create_erp_agent():
    """
    Create and return the ERP Operations Agent.

    This function performs the reusable setup needed by both:
    - the interactive CLI in agent.py
    - the scripted workflows in scripts/

    It returns:
    - agent: the LangChain/LangGraph agent object
    - tools: the list of tools loaded from the MCP server

    Why this is async:
    - MCP tool loading involves communication with another process.
    - LangChain tool calls can be asynchronous.
    """
    # Load the system prompt that defines the agent's role and rules.
    system_prompt = load_system_prompt()

    # Create the OpenAI chat model.
    #
    # temperature=0 makes the model more deterministic.
    # That is useful for operational workflows where you want repeatable behavior.
    model = ChatOpenAI(
        model="gpt-4.1-mini",
        temperature=0,
    )

    # Configure the MCP client.
    #
    # MultiServerMCPClient can connect to multiple MCP servers.
    # Here, we only connect to one server named "olist_erp".
    client = MultiServerMCPClient(
        {
            "olist_erp": {
                # Use the Python interpreter from the MCP repo's venv.
                "command": MCP_PYTHON_PATH,

                # Run the MCP server module.
                "args": ["-m", "src.olist_erp_mcp.server"],

                # Use stdio transport.
                # That means the agent and MCP server communicate through
                # standard input/output pipes.
                "transport": "stdio",

                # Run the command from the MCP repo root.
                # This lets the MCP server load its own .env file and imports.
                "cwd": MCP_WORKING_DIR,

                # Add the MCP repo root to Python's import path.
                "env": {
                    "PYTHONPATH": ".",
                },
            }
        }
    )

    # Ask the MCP server what tools it exposes.
    # The adapter converts MCP tools into LangChain-compatible tools.
    tools = await client.get_tools()

    # Create the agent.
    #
    # create_agent builds a LangGraph-backed agent that can:
    # - read the user prompt
    # - decide which tools to call
    # - call tools
    # - observe tool results
    # - produce a final answer
    agent = create_agent(
        model=model,
        tools=tools,
        system_prompt=system_prompt,
    )

    return agent, tools


async def run_agent_prompt(prompt: str, debug_trace: bool | None = None) -> dict[str, Any]:
    """
    Run one prompt through the ERP Operations Agent.

    This is used by the scripted workflow files.

    Example:
        await run_agent_prompt("Find 3 late shipments...")

    Parameters:
    - prompt: the business instruction to give the agent
    - debug_trace: whether to print tool call details

    Returns:
    - the full LangChain result dictionary
    """
    # If debug_trace was not explicitly passed, read it from .env.
    if debug_trace is None:
        debug_trace = is_debug_trace_enabled()

    # Create the agent and load the MCP tools.
    agent, tools = await create_erp_agent()

    # Print the tools so the user can confirm the MCP connection worked.
    print("\nLoaded MCP tools:")
    for tool in tools:
        print(f"- {tool.name}")

    # Invoke the agent with a single user message.
    #
    # LangChain agents expect messages in a list.
    # The message format is:
    # {"role": "user", "content": "..."}
    result = await agent.ainvoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ]
        }
    )

    # The final message is normally the agent's final answer.
    final_message = result["messages"][-1]

    print("\nAgent:")
    print(final_message.content)
    print()

    # Optionally print the tool trace.
    if debug_trace:
        print_debug_trace(result)

    return result