---
name: lunchbox-genie-orchestration
description: "Manages session state transitions, user feedback loops, and delegates tasks to the Dietitian, Grocery, and Favorites subagents."
---

# Lunchbox Genie Session Orchestration

This skill defines the state machine rules and subagent communication logic for directing a weekly school lunch planning session.

## State Machine Rules

The orchestrator must transition through states sequentially based on user progress:

1. **State: DRAFTING**
   - **Trigger**: User starts a session.
   - **Actions**: 
     - Call `recipe_favorites_log` to fetch existing favorites.
     - Compile user preferences (kid count, allergy notes, dislikes).
     - Delegate to `pediatric_dietetics_planner` to generate the first menu draft.
     - Move to **REFINEMENT**.

2. **State: REFINEMENT**
   - **Trigger**: First draft is presented.
   - **Actions**:
     - Loop feedback from the user.
     - If changes are requested, send the delta to `pediatric_dietetics_planner`.
     - Remain in this state until user inputs approval (e.g. "looks good", "approve").

3. **State: APPROVAL**
   - **Trigger**: User approves menu.
   - **Actions**:
     - Check if user highlighted any new recipes to save.
     - If so, call `recipe_favorites_log` to persist them.
     - Move to **LIST_GENERATION**.

4. **State: LIST_GENERATION**
   - **Trigger**: Menu approved.
   - **Actions**:
     - Extract menu recipes, portion sizes, and kid count.
     - Call `grocery_list_scaler` to build the consolidated shopping list.
     - Present the final approved menu and shopping list to the user.

## Subagent Delegation Interface
- Use standard `invoke_subagent` calls.
- Forward all necessary context (number of kids, allergies) in JSON parameters to avoid subagents asking duplicate questions.
