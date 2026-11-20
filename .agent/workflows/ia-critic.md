---
description: Workflow for critical review of implementation plans by the Agent Auditor
agent: auditor
skills: [coding-standards, agentic-memory]
validation: |
  - Verify that the plan complies with Core/GUI separation
  - Validate that no obvious technical debt is introduced
  - Confirm that lessons from AGENT_LESSONS.md were taken into account
---

# Workflow: AI Critic (Implementation Plan Audit)

This workflow must be executed after creating an `implementation_plan.md` but before starting `EXECUTION`.

### Steps

1. **Critical Context Loading**:
   🤖 **Agent Action**: Load `AGENT_LESSONS.md` and look for lessons relevant to the current plan.

2. **Compliance Analysis**:
   🤖 **Agent Action**: Contrast the plan against coding standards (Pathlib, Typing, Google Docstrings).

3. **Risk Detection**:
   - Does it introduce UI/framework dependencies in the domain layer?
   - Does it propose changes that break compatibility with the target runtime/framework version?
   - Is the verification plan sufficient?

4. **Verdict Issuance**:
   🤖 **Agent Action**: Generate an audit report indicating:
   - **PASSED**: The plan is solid.
   - **FAILED**: The plan requires specific corrections.
   - **OBSERVATIONS**: Non-critical improvement suggestions.

---
*Philosophy: It is better to find an error in the blueprint than in the building.*
