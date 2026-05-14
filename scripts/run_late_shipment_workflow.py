"""
run_late_shipment_workflow.py

This script runs a repeatable late-shipment triage workflow.

Why this script exists:
- A manual chat prompt is flexible but not repeatable.
- A script gives you a one-command demo.
- This is closer to how an enterprise automation might work.

Workflow:
1. Find shipments delayed by more than 10 days.
2. Inspect each related order.
3. Inspect each related invoice.
4. Create fulfillment review tasks.
5. Add operational notes.
6. Summarize what happened in a human-readable report.
"""

import asyncio

from agent_factory import run_agent_prompt


PROMPT = """
Run a late shipment triage workflow.

Find the top 3 shipments delayed by more than 10 days.

For each shipment:
1. Inspect the order.
2. Inspect the invoice.
3. Create a high-priority fulfillment review task.
4. Add an operational note explaining why it was flagged.

Your final response must be human-readable and use this exact structure:

## Late Shipment Triage Summary

### What I reviewed
Briefly describe the search criteria and how many shipments were reviewed.

### Records reviewed
For each shipment, include:
- Order ID
- Customer city/state
- Estimated delivery date
- Actual delivery date
- Delay in days
- Invoice total
- Payment status

### Actions taken
For each shipment, include:
- Task created
- Task priority
- Note added

### Business interpretation
Explain in plain English what this means operationally.

### Recommended next step
Give one practical next step for the fulfillment team.

Do not only say that you created tasks. Include the actual order IDs and key facts.
"""


async def main() -> None:
    """
    Run the late shipment workflow.
    """
    print("\n" + "=" * 80)
    print("LATE SHIPMENT TRIAGE WORKFLOW")
    print("=" * 80)
    print(
        "\nThis workflow finds materially late shipments, inspects the related "
        "orders and invoices, creates fulfillment review tasks, and writes "
        "operational notes back to Supabase."
    )
    print("\nRunning agent workflow...\n")

    await run_agent_prompt(PROMPT)

    print("\nWorkflow complete.")
    print("Check Supabase tables: agent_tasks and agent_notes.")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())