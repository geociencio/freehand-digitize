---
name: agentic-memory
description: This skill allows the agent to manage its own semantic memory, extracting lessons, patterns, and user preferences to improve long-term effectiveness. Use at the end of each significant session, when detecting repetitive error patterns or user preferences.
---

# Skill: Agentic Memory (Brain)

This skill enables the agent to manage its own semantic memory by extracting lessons, patterns, and user preferences to enhance long-term effectiveness.

## Extraction Guidelines

The agent must actively look for the following elements during interaction:

1.  **Error Patterns**: Solutions to bugs that took more than 3 attempts or required deep investigation.
2.  **Implicit Preferences**: Style or architectural decisions that the user repeatedly approves.
3.  **Technical Hotspots**: Areas of code that are difficult to test or refactor.
4.  **Design Decisions**: Justifications for why one implementation was chosen over another.

## Update Protocol (`AGENT_LESSONS.md`)

At the end of each significant session, the agent must:

1.  **Verify Path**: Ensure you are NOT in a framework or scaffold directory. All persistence must happen in the project root's state directory (`.agent-state/`).
2.  **Target Metrics**: Update `.agent-state/memory/agent_metrics.json` (NEVER a scaffold file).
3.  **Synthesize**: Summarize findings in entries of at most 3 lines in `AGENT_LESSONS.md`.
4.  **Categorize**: Use tags such as `[TECHNICAL]`, `[USER_PREFERENCE]`, `[ARCHITECTURE]`.
5.  **Structure**: Maintain a YAML-friendly format for future RAG integrations.

## Structured Entry Example

```yaml
- date: 2026-02-05
  category: TECHNICAL
  topic: Geometry Mocking
  lesson: "A geometry method fails in simple mocks; requires domain context injection."
  action: "Use the domain factory/constructor whenever possible to avoid manual mocks."
```

## Pre-flight Self-Audit

Before concluding any task or workflow, the agent must perform a self-audit:
1. **Lessons Check**: "Have I applied relevant lessons from `AGENT_LESSONS.md`?"
2. **Context Integrity**: "Does my solution follow the project's architectural standards (e.g., Core/GUI separation)?"
3. **Structured Output**: "Does my final response provide a clear, structured summary of what was done and tested?"

---
*Agentic Forge skill — manages semantic memory for the consuming project.*
