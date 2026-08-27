---
name: codex-self-improvement
description: Review recent work to identify repeated manual workflows worth packaging, then create only high-confidence missing skills, custom subagents, commands, or automations. Use when the user asks Codex to look back over recent sessions, memories, rollout summaries, Chronicle, or existing agent assets to find recurring work; when they mention Codex self-improvement; or when they ask to package repeated workflows into reusable agent capabilities.
---

# Codex Self Improvement

## Overview

Find repeated, costly, stable workflows in recent work history and turn only the best-evidenced gaps into narrow reusable agent assets. Keep the work evidence-led: first shortlist candidates, then create or extend the smallest appropriate item.

## Workflow

1. Define the review window. Default to the last 30 days; if less history exists, use all available history. State the window and any unavailable sources.
2. Collect evidence in this order:
   - Recent Codex sessions and task summaries.
   - Codex Memories and rollout summaries.
   - Chronicle, if enabled. Use it for discovery only; confirm important details in the relevant source system when possible.
   - Existing skills, custom agents, commands, and automations.
3. Look broadly across coding, research, writing, planning, communication, operations, analysis, and personal administration. Do not restrict the search to software tasks unless the user does.
4. De-duplicate against existing assets before recommending creation. Prefer extending a suitable existing skill, subagent, command, or automation over adding a near-duplicate.
5. Build a compact shortlist before creating anything.
6. Create or extend only high-confidence missing items. Skip speculative, overlapping, sensitive, poorly evidenced, or one-off workflows.
7. Validate every created or modified asset with the appropriate local validator or a direct smoke test.

## Candidate Test

Package a workflow only when all conditions hold:

- It occurred at least twice, or is clearly likely to recur and costly to repeat.
- It has stable inputs, a repeatable procedure, and a clear output or stopping condition.
- Packaging it would materially improve speed, quality, consistency, or reliability.
- It is not already adequately covered by an existing skill, subagent, command, script, or automation.

## Choose The Smallest Form

- **Skill**: Use for a reusable workflow, playbook, domain guide, or tool/file-format procedure that an agent can follow interactively.
- **Custom subagent**: Use for a bounded specialist role or investigation task that benefits from delegation and context isolation.
- **Automation**: Use for a scheduled or recurring check, report, reminder, monitor, or deterministic scriptable task.
- **Extend existing**: Use when a current asset covers most of the job and only needs a narrower trigger, missing step, script, or reference.
- **Skip**: Use when the workflow is one-off, ambiguous, overly broad, sensitive, poorly evidenced, or already covered well enough.

When the recommended form is a skill, use the available skill creation workflow. Keep `SKILL.md` concise, put detailed references or deterministic helpers in bundled resources only when they are actually needed, and validate the skill folder after edits.

## Shortlist Format

Produce the shortlist before creating assets:

```markdown
| Repeated workflow | Evidence and dates | Frequency / confidence | Recommended form | Worth creating? |
| --- | --- | --- | --- | --- |
| ... | ... | ... | skill / subagent / automation / extend existing / skip | Why or why not |
```

Keep evidence specific enough to audit: include session dates, memory or rollout names, file paths, command names, or existing asset paths when available. If exact dates are unavailable, say so instead of inventing them.

## Creation Rules

Before writing files:

- State which shortlist items will be created, extended, or skipped.
- Confirm the target directory or infer it from the repo's existing conventions. If there is no clear convention and writing outside the workspace would be required, ask.
- Reuse existing scripts, references, templates, and style where available.
- Keep each created asset narrow enough that its trigger and stopping condition are obvious.

Do not create broad meta-skills, overlapping variants, speculative automations, or documentation about the creation process. The asset itself should be the durable output.

## Final Response

Finish with:

- What was created or extended, with paths.
- What was deliberately skipped and why.
- What needs more evidence before packaging.
- What validation was run and what remains unverified.
