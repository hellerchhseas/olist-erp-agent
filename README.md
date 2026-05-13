# Olist ERP Agent

LangChain/LangGraph ERP Operations Agent that uses a local MCP server to interact with a simulated ERP backend built from the Olist Brazilian E-Commerce dataset.

This repo is the agent/application layer.

Companion repos:

- `olist-erp-demo` — data cleaning, Supabase tables, SQL views
- `olist-erp-mcp` — MCP server exposing ERP business tools
- `olist-erp-agent` — LangChain/LangGraph agent consuming the MCP tools

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