"""
run_finance_exception_workflow.py

This script runs a repeatable finance exception review workflow.

Why this script exists:
- Finance teams often review invoice, payment, and order exceptions.
- The agent can find exceptions, inspect related records, and create follow-up tasks.
- This simulates finance operations or order-to-cash exception handling.

Workflow:
1. Find invoice exceptions.
2. Inspect selected exception records.
3. Inspect related invoices.
4. Inspect related orders.
5. Create finance review tasks when needed.
6. Add operational notes.
7. Summarize the issue in a human-readable report.
"""

import asyncio

from agent_factory import run_agent_prompt


PROMPT = """
Run a finance exception review workflow.

Find 5 invoice exceptions.

Inspect the top 3 invoice exceptions in detail.

For each invoice exception:
1. Inspect the invoice.
2. Inspect the related order.
3. Determine whether finance follow-up is required.
4. If follow-up is required, create a finance review task.
5. Add an operational note explaining the issue.

Your final response must be human-readable and use this exact structure:

## Finance Exception Review Summary

### What I reviewed
Briefly describe the search criteria and how many invoice exceptions were reviewed.

### Exceptions reviewed
For each invoice exception, include:
- Invoice ID
- Order ID
- Customer city/state
- Order status
- Invoice total
- Payment total
- Payment status
- Delivery status
- Delivery delay days if available
- Exception type or reason

### Actions taken
For each invoice exception, include:
- Whether finance follow-up was required
- Task created if applicable
- Task priority if applicable
- Note added

### Business interpretation
Explain in plain English what these finance exceptions mean operationally.

### Recommended next step
Give one practical next step for the finance operations team.

Do not only say that you created tasks. Include the actual invoice IDs, order IDs, and key facts.
"""


async def main() -> None:
    """
    Run the finance exception review workflow.
    """
    print("\n" + "=" * 80)
    print("FINANCE EXCEPTION REVIEW WORKFLOW")
    print("=" * 80)
    print(
        "\nThis workflow finds invoice exceptions, inspects related invoices "
        "and orders, creates finance review tasks when needed, and writes "
        "operational notes back to Supabase."
    )
    print("\nRunning agent workflow...\n")

    await run_agent_prompt(PROMPT)

    print("\nWorkflow complete.")
    print("Check Supabase tables: agent_tasks and agent_notes.")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
    