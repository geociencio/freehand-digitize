---
description: Start the Autonomous AI Developer Pipeline sequence for a new feature.
agent: architect
skills: [coding-standards, testing-standards]
stop_conditions:
  - "Tests fail after 3 consecutive fix attempts → escalate to user"
  - "Architectural conflict detected between domain and UI layers → stop and request review"
  - "Implementation plan diverges >30% from approved Technical_Specification.md → re-plan"
---
# Build Feature Autonomous Pipeline

When the user types `/build-feature <requirement>`, orchestrate the development process strictly using `AGENTS.md` and the modular skills.

### Execution Sequence:

1. **Strategic Planning Mode**
   Act as the **@architect**. Deeply analyze the `<requirement>`. Use the project's domain
   and coding standards skills to draft a robust implementation plan.
   - **Important**: Save this plan as `docs/plans/Technical_Specification.md`.
   - **Approval Gate**: You MUST pause execution and eagerly ask the user: "Do you approve of this architecture? You can add comments directly to `Technical_Specification.md` if you want me to rethink any part."
   *(Wait for the user to explicitly type "Approved" or apply their requested feedback before moving to step 2).*

1.5. **Technical Critique (Architect vs. Auditor) 🤖**
   - **Agent Reflection**: Activate the **@auditor** role.
   - **Challenge the Plan**: Identify 3 potential failure points or edge cases in the proposed strategy.
   - **Mitigation**: The @architect must address these points before presenting the plan to the user.
   - **Hallucination Hunt**: Verify that all proposed tool calls and file paths are valid.

2. **Autonomous Execution Phase**
   Shift context. Act as the **@architect** again (now acting as the developer), but strictly follow the approved `Technical_Specification.md`.
   - Write the business logic and the UI components according to the project's architectural standard (domain logic decoupled from the UI layer).

3. **Autonomous QA & Bug-Hunting Phase**
   Shift context. Act as the **@qa_engineer**.
   - Write the corresponding isolated unit tests or integration tests.
   - You MUST run the project's full test suite (and its containerized test command) to guarantee integration within the target environment.
   - Find and fix any dependency mismatches, unhandled errors, or edge cases. Do not stop until all tests pass.

4. **Integration & Handover**
   Shift context to the **@auditor**.
   - Review that the code maintains the project's architectural boundaries (e.g. domain/UI separation).
   - **Quality Check**: Run the project's static analyzer to ensure no new method exceeds the project complexity limit.
   - Once successfully checked, generate an output confirming the feature is ready to be committed!

---

## ⛔ Stop Conditions (Human Escalation Required)

| Condition | Action |
|---|---|
| Tests fail after **3+ fix attempts** on the same root cause | Stop. Report exact error. Ask user for direction. |
| A domain module needs to import from the UI layer | Stop immediately. This violates the architectural boundary. Request architectural review. |
| The approved `Technical_Specification.md` no longer matches what was built | Stop. Present delta. Ask user to re-approve or adjust scope. |
| A background thread needs a live UI object | Stop. Propose a serializable/plain-data alternative. Wait for approval. |
