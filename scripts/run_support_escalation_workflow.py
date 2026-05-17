"""
run_support_escalation_workflow.py

This script runs a repeatable customer support escalation workflow.

Why this script exists:
- High-priority support cases represent dissatisfied customers.
- The agent should inspect the support case, order, and invoice context.
- If follow-up is needed, the agent creates a support task and adds a note.

Workflow:
1. Find high-priority support cases.
2. Inspect related orders.
3. Inspect related invoices.
4. Create support follow-up tasks.
5. Add operational notes.
6. Summarize the issue in a human-readable report.
"""

import asyncio

from agent_factory import run_agent_prompt


PROMPT = """
Run a customer support escalation workflow.

Find 3 high-priority support cases.

For each support case:
1. Inspect the related order.
2. Inspect the related invoice.
3. Before creating a support follow-up task, check whether an open task already exists for the support case.
4. Use entity_type = "support_case" and entity_id = case_id when checking for existing tasks.
5. If an open task already exists:
   - Do not create a duplicate task.
   - Add an operational note saying the case was re-reviewed and the existing task remains open.
   - Include the existing task ID in your final response.
6. If no open task exists:
   - Create a high-priority support follow-up task.
   - Add an operational note explaining the likely customer issue.

Your final response must be human-readable and use this exact structure:

## Customer Support Escalation Summary

### What I reviewed
Briefly describe the search criteria and how many support cases were reviewed.

### Cases reviewed
For each support case, include:
- Case ID
- Order ID
- Review score
- Customer city/state if available
- Order status
- Delivery status or timing if available
- Invoice total
- Payment status
- Customer comment or issue summary if available

### Actions taken
For each case, include:
- Whether an existing open task was found
- Existing task ID if applicable
- Whether a new task was created
- Task priority if a task was created
- Note added

### Business interpretation
Explain in plain English what these cases suggest operationally.

### Recommended next step
Give one practical next step for the customer support team.

Do not only say that you created tasks. Include the actual case IDs, order IDs, and key facts.
"""


async def main() -> None:
    """
    Run the customer support escalation workflow.
    """
    print("\n" + "=" * 80)
    print("CUSTOMER SUPPORT ESCALATION WORKFLOW")
    print("=" * 80)
    print(
        "\nThis workflow finds high-priority customer support cases, inspects "
        "the related orders and invoices, creates support follow-up tasks, "
        "and writes operational notes back to Supabase."
    )
    print("\nRunning agent workflow...\n")

    await run_agent_prompt(PROMPT)

    print("\nWorkflow complete.")
    print("Check Supabase tables: agent_tasks and agent_notes.")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())