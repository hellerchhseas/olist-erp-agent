import asyncio
from pathlib import Path

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI


# ------------------------------------------------------------
# Load environment variables from .env
# ------------------------------------------------------------
# This repo's .env should contain:
#
# OPENAI_API_KEY=your_openai_api_key_here
#
# We do NOT put Supabase credentials in this agent repo.
# Supabase credentials live in the MCP repo's .env because the MCP
# server is the component that talks directly to Supabase.
load_dotenv()


# ------------------------------------------------------------
# Local MCP server configuration
# ------------------------------------------------------------
# This agent will launch your local Olist ERP MCP server as a subprocess.
#
# The MCP server lives in a separate repo:
#
#   ~/dev/olist-erp-mcp
#
# That repo contains:
# - the MCP server
# - the Supabase client
# - the ERP business tools
#
# The agent does not import those tools directly. Instead, it connects
# to the MCP server and receives the tools through the MCP protocol.
MCP_SERVER_PATH = "/Users/christianheller/dev/olist-erp-mcp/src/olist_erp_mcp/server.py"
MCP_WORKING_DIR = "/Users/christianheller/dev/olist-erp-mcp"
MCP_PYTHON_PATH = "/Users/christianheller/dev/olist-erp-mcp/.venv/bin/python"


def load_system_prompt() -> str:
    """
    Load the ERP Operations Agent system prompt from a markdown file.

    Keeping the prompt in a separate file makes it easier to edit the
    agent's behavior without modifying Python code.
    """
    return Path("prompts/erp_operations_agent.md").read_text()


async def main() -> None:
    """
    Main async entrypoint for the ERP Operations Agent.

    High-level flow:
    1. Load the system prompt.
    2. Create the OpenAI chat model.
    3. Launch/connect to the local MCP server.
    4. Load MCP tools as LangChain-compatible tools.
    5. Create a LangChain/LangGraph agent using those tools.
    6. Start a simple command-line chat loop.
    """

    # ------------------------------------------------------------
    # 1. Load the system prompt
    # ------------------------------------------------------------
    # The system prompt tells the agent how to behave:
    # - act like an ERP operations analyst
    # - use tools before making factual claims
    # - create notes/tasks when follow-up is needed
    system_prompt = load_system_prompt()

    # ------------------------------------------------------------
    # 2. Create the LLM
    # ------------------------------------------------------------
    # ChatOpenAI is the LangChain wrapper around OpenAI chat models.
    #
    # temperature=0 makes the model more deterministic, which is better
    # for tool-using business workflows where we want consistent behavior.
    #
    # You can swap this model later if needed.
    model = ChatOpenAI(
        model="gpt-4.1-mini",
        temperature=0,
    )

    # ------------------------------------------------------------
    # 3. Configure the MCP client
    # ------------------------------------------------------------
    # MultiServerMCPClient can connect to one or more MCP servers.
    #
    # Here we configure one MCP server named "olist_erp".
    #
    # The command below launches the MCP server using the Python executable
    # from the MCP repo's virtual environment:
    #
    #   /Users/christianheller/dev/olist-erp-mcp/.venv/bin/python
    #
    # The args run the MCP server module:
    #
    #   -m src.olist_erp_mcp.server
    #
    # The cwd is important. It tells the subprocess to run from the MCP
    # repo root so that:
    # - the MCP repo's .env can be loaded
    # - Python imports work correctly
    #
    # The PYTHONPATH=. environment variable tells Python that the current
    # working directory should be treated as an import root.
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
    # 4. Load tools from the MCP server
    # ------------------------------------------------------------
    # This asks the MCP server:
    #
    #   "What tools do you expose?"
    #
    # The MCP adapter converts those MCP tools into LangChain-compatible
    # tools that the agent can call.
    #
    # Expected tools include:
    # - list_late_shipments_tool
    # - get_order_tool
    # - get_invoice_tool
    # - list_high_priority_support_cases_tool
    # - list_high_risk_sellers_tool
    # - create_agent_task_tool
    # - add_agent_note_tool
    tools = await client.get_tools()

    # Print loaded tools so we can verify that MCP connection worked.
    print("\nLoaded MCP tools:")
    for tool in tools:
        print(f"- {tool.name}")

    # ------------------------------------------------------------
    # 5. Create the agent
    # ------------------------------------------------------------
    # create_agent builds a LangGraph-backed agent runtime.
    #
    # The agent receives:
    # - the OpenAI model
    # - the MCP tools
    # - the ERP operations system prompt
    #
    # The agent can now decide which tools to call based on the user's
    # request. For example, if the user asks for late shipments, the agent
    # should call list_late_shipments_tool.
    agent = create_agent(
        model=model,
        tools=tools,
        system_prompt=system_prompt,
    )

    # ------------------------------------------------------------
    # 6. Start a simple CLI chat loop
    # ------------------------------------------------------------
    # This is intentionally basic:
    # - read user input from terminal
    # - send it to the agent
    # - print the final response
    #
    # Later, this could be replaced with:
    # - Streamlit
    # - FastAPI
    # - a web frontend
    # - Slack/Teams integration
    # - scheduled workflows
    print("\nERP Operations Agent")
    print("Type a question. Type 'exit' or 'quit' to stop.\n")

    while True:
        # Read input from the user.
        user_input = input("You: ").strip()

        # Exit condition for the CLI loop.
        if user_input.lower() in {"exit", "quit"}:
            break

        # --------------------------------------------------------
        # Invoke the agent
        # --------------------------------------------------------
        # LangChain agents expect a message list.
        #
        # The user message is passed as:
        #
        # {
        #   "role": "user",
        #   "content": user_input
        # }
        #
        # The agent may then:
        # - reason about the request
        # - call one or more MCP tools
        # - observe tool results
        # - call additional tools if needed
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
        # Print the final agent response
        # --------------------------------------------------------
        # result["messages"] contains the full conversation trace:
        # - user message
        # - model/tool-call messages
        # - tool result messages
        # - final assistant message
        #
        # The last message is normally the final answer.
        final_message = result["messages"][-1]

        print("\nAgent:")
        print(final_message.content)
        print()


# ------------------------------------------------------------
# Script entrypoint
# ------------------------------------------------------------
# asyncio.run(main()) starts the async event loop and runs the agent.
#
# We use async because MCP tool calls and LangChain agent execution are
# asynchronous operations.
if __name__ == "__main__":
    asyncio.run(main())