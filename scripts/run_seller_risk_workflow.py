"""
run_seller_risk_workflow.py

This script runs a repeatable seller/vendor risk review workflow.

Why this script exists:
- Seller performance is a realistic enterprise operations use case.
- The agent can identify risky sellers and create review tasks.
- This simulates vendor management, procurement operations, or marketplace operations.

Workflow:
1. Find high-risk sellers.
2. Inspect seller performance.
3. Create seller review tasks.
4. Add operational notes.
5. Summarize seller risk in a human-readable report.
"""

import asyncio

from agent_factory import run_agent_prompt


PROMPT = """
Run a seller risk review workflow.

Find 3 high-risk sellers.

For each high-risk seller:
1. Inspect seller performance.
2. Before creating a seller review task, check whether an open task already exists for the seller.
3. Use entity_type = "seller" and entity_id = seller_id when checking for existing tasks.
4. If an open task already exists:
   - Do not create a duplicate task.
   - Add an operational note saying the seller was re-reviewed and the existing task remains open.
   - Include the existing task ID in your final response.
5. If no open task exists:
   - Create a high-priority seller review task.
   - Add an operational note explaining the seller risk.

Your final response must be human-readable and use this exact structure:

## Seller Risk Review Summary

### What I reviewed
Briefly describe the search criteria and how many sellers were reviewed.

### Sellers reviewed
For each seller, include:
- Seller ID
- Seller city/state
- Order count
- Order line count
- Product revenue
- Freight total
- Average review score
- Late delivery count
- Late delivery rate
- Seller risk level if available

### Actions taken
For each seller, include:
- Whether an existing open task was found
- Existing task ID if applicable
- Whether a new task was created
- Task priority if a task was created
- Note added

### Business interpretation
Explain in plain English what these seller risks mean operationally.

### Recommended next step
Give one practical next step for the vendor management or fulfillment team.

Do not only say that you created tasks. Include the actual seller IDs and key performance facts.
"""

async def main() -> None:
    """
    Run the seller risk review workflow.
    """
    print("\n" + "=" * 80)
    print("SELLER RISK REVIEW WORKFLOW")
    print("=" * 80)
    print(
        "\nThis workflow finds high-risk sellers, inspects seller performance, "
        "creates seller review tasks, and writes operational notes back to "
        "Supabase."
    )
    print("\nRunning agent workflow...\n")

    await run_agent_prompt(PROMPT)

    print("\nWorkflow complete.")
    print("Check Supabase tables: agent_tasks and agent_notes.")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())