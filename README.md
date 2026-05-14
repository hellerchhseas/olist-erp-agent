# Olist ERP Agent

LangChain/LangGraph ERP Operations Agent that uses a local MCP server to interact with a simulated ERP backend built from the Olist Brazilian E-Commerce dataset.

This repo is the agent/application layer.

### Companion Repos
*   **olist-erp-demo:** data cleaning, Supabase tables, SQL views
*   **olist-erp-mcp:** MCP server exposing ERP business tools
*   **olist-erp-agent:** LangChain/LangGraph agent consuming the MCP tools

---

## Architecture

```text
User
↓
LangChain/LangGraph ERP Operations Agent
↓
langchain-mcp-adapters
↓
Local Olist ERP MCP Server
↓
Supabase ERP Views and Agent Tables

Agent Purpose
The ERP Operations Agent investigates operational issues across:
- Invoices
- Orders
- Shipments
- Support cases
- Customers
- Seller/vendor performance

It can retrieve facts, inspect exceptions, create follow-up tasks, and add operational notes.

Current MCP Tools used by the Agent
- Read / Lookup Tools
- get_invoice_tool
- get_order_tool
- get_customer_account_summary_tool
- get_seller_performance_tool
- Exception / List Tools
- list_late_shipments_tool
- list_high_priority_support_cases_tool
- list_high_risk_sellers_tool
- list_invoice_exceptions_tool
- Write / Action Tools

add_agent_note_tool

create_agent_task_tool

Setup
Create virtual environment:

Bash
python3.11 -m venv .venv
source .venv/bin/activate


2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Create `.env`:**
    ```bash
    OPENAI_API_KEY=your_openai_api_key_here
    DEBUG_TRACE=false
    
> **Note:** Do not commit `.env`. Set `DEBUG_TRACE=true` when you want the CLI to print tool-call traces after each agent response.
Required Local Dependency
This agent expects the MCP repo to exist locally at:
/Users/christianheller/dev/olist-erp-mcp

The MCP repo must have its own .env with:

SUPABASE_URL=your_supabase_url

SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key

The agent repo does not need Supabase credentials. The agent talks to the MCP server, and the MCP server talks to Supabase.

Run the Agent
Bash
cd ~/dev/olist-erp-agent
source .venv/bin/activate
python agent.py
Debug Trace Mode
The agent supports an optional debug trace mode controlled by .env:
DEBUG_TRACE=true

When enabled, each agent turn prints:

Tool calls selected by the model

Tool arguments

Tool result previews

This is useful for demos and debugging because it shows the operational path, for example:

Tool call 1: list_late_shipments_tool

Tool call 2: get_order_tool

Tool call 3: get_invoice_tool

Tool call 4: create_agent_task_tool

Tool call 5: add_agent_note_tool

To disable tracing, set DEBUG_TRACE=false.

Example Prompts
Late shipment workflow: Find the top 3 shipments delayed by more than 10 days. For each one, inspect the order and invoice, create a fulfillment review task, add an operational note, and summarize what you did.

Customer support workflow: Find 3 high-priority support cases. For each one, inspect the order and invoice, create a support follow-up task, and summarize the likely issue.

Seller risk workflow: Find 3 high-risk sellers. For the worst one, inspect seller performance, create a seller review task, and add a note explaining the risk.

Finance exception workflow: Find 5 invoice exceptions. Inspect the first one and create a finance review task if follow-up is required.

Successful Test Result
A successful late-shipment workflow should:

Call list_late_shipments_tool

Call get_order_tool

Call get_invoice_tool

Call create_agent_task_tool

Call add_agent_note_tool

Write rows to Supabase agent_tasks and agent_notes

Return a concise business summary

Repo Structure
Plaintext
olist-erp-agent/
├── .env.example
├── .gitignore
├── README.md
├── agent.py
├── prompts/
│   └── erp_operations_agent.md
└── requirements.txt
Security Notes
Do not commit .env.

This repo should only contain the OpenAI API key in local .env.

Supabase credentials belong in the MCP repo’s local .env, not here.

Next Improvements
Add separate workflow scripts for support, finance, and seller risk

Add structured output for task summaries

Add LangGraph state/checkpointing

Add a lightweight Streamlit UI

Split into specialized agents later

## Scripted workflows

The project includes repeatable workflow scripts for demo and testing.

Run from the repo root:

    cd ~/dev/olist-erp-agent
    source .venv/bin/activate

For clean business-readable output, use:

    DEBUG_TRACE=false

For learning/debugging output, use:

    DEBUG_TRACE=true

### Late shipment triage

    PYTHONPATH=. python scripts/run_late_shipment_workflow.py

This workflow finds materially late shipments, inspects related orders and invoices, creates fulfillment review tasks, adds operational notes, and prints a structured operations summary.

### Customer support escalation

    PYTHONPATH=. python scripts/run_support_escalation_workflow.py

This workflow finds high-priority support cases, inspects related orders and invoices, creates support follow-up tasks, adds operational notes, and prints a structured support escalation summary.

### Seller risk review

    PYTHONPATH=. python scripts/run_seller_risk_workflow.py

This workflow finds high-risk sellers, inspects seller performance, creates seller review tasks, adds operational notes, and prints a structured seller risk summary.

### Finance exception review

    PYTHONPATH=. python scripts/run_finance_exception_workflow.py

This workflow finds invoice exceptions, inspects related invoices and orders, creates finance review tasks when needed, adds operational notes, and prints a structured finance exception summary.