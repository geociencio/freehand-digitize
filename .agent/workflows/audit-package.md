---
description: Run the project's own quality analyzer on its source code for self-audit.
agent: auditor
skills: [coding-standards, testing-standards]
validation: |
  - Verify analysis completes without errors
  - Confirm no critical/blocking issues
  - Review the generated analysis summary
---

# Workflow: Audit Package (Self-Analysis)

Runs the project's static analyzer on its own source code to detect quality
regressions, security issues, and standards violations.

### 1. Run Full Analysis
// turbo
```bash
# project's self-analysis command (e.g. a custom analyzer or linter suite)
```

### 2. Review Results

🤖 **Agent Action**: Read and interpret the analysis output.

- Check the generated summary report for overall scores
- Review any `HIGH` or `CRITICAL` severity issues
- Compare scores against the previous baseline in `.agent-state/memory/agent_metrics.json`

### 3. Triage Issues

| Severity | Action |
|----------|--------|
| CRITICAL | Fix immediately, block release |
| HIGH | Log in `task.md`, fix this session |
| MEDIUM | Log in `next_steps.md` for next phase |
| LOW | Accept or log as technical debt |

### 4. Update Metrics
After triage, update `.agent-state/memory/agent_metrics.json` with the new scores.

### Expected Results
- All tests passing
- Security score: 100/100
- Maintainability: at or above the project threshold
- No new CRITICAL or HIGH issues
