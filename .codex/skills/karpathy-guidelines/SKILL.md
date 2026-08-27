---
name: karpathy-guidelines
description: Behavioral guidelines to reduce common LLM coding mistakes. Use when writing, reviewing, debugging, or refactoring code to surface assumptions, avoid overcomplication, keep edits surgical, and define verifiable success criteria.
---

# Karpathy Guidelines

## Overview

Use these guidelines to reduce common coding-agent failures: silent assumptions, hidden confusion, bloated abstractions, unrelated edits, and vague stopping conditions. They are adapted from `multica-ai/andrej-karpathy-skills`, which cites Andrej Karpathy's observations on LLM coding pitfalls.

Tradeoff: these guidelines bias toward caution over speed. For trivial one-line tasks, use judgment and keep the process lightweight.

## 1. Think Before Coding

Do not assume or hide confusion. Surface tradeoffs before implementation.

- State assumptions explicitly when they affect the solution.
- If multiple interpretations exist, present them instead of silently choosing one.
- If a simpler approach exists, say so and push back when warranted.
- If something is unclear enough to risk the outcome, stop, name the uncertainty, and ask.

## 2. Simplicity First

Write the minimum code that solves the actual request. Do not add speculative flexibility.

- Do not add features beyond what was asked.
- Do not add abstractions for single-use code.
- Do not add configurability that was not requested.
- Do not add elaborate handling for impossible or irrelevant scenarios.
- If the implementation is much larger than the problem, simplify before finishing.

Ask: would a senior engineer call this overcomplicated? If yes, reduce it.

## 3. Surgical Changes

Touch only what the task requires. Clean up only consequences of your own edits.

- Do not "improve" adjacent code, comments, formatting, or naming unrelated to the request.
- Do not refactor code that is not broken unless refactoring is the task.
- Match existing style even when you would personally choose a different style.
- If you notice unrelated dead code or design problems, mention them; do not delete or rewrite them unless asked.
- Remove imports, variables, functions, or files that your own changes made unused.
- Do not remove pre-existing dead code unless the user asks.

Test: every changed line should trace directly to the user's request or to validation required by that request.

## 4. Goal-Driven Execution

Define success criteria and loop until verified.

- Convert "fix the bug" into: reproduce it, make the smallest fix, verify it no longer reproduces.
- Convert "add validation" into: define invalid cases, add or run checks, verify behavior.
- Convert "refactor" into: preserve behavior, run checks before and after when possible.

For multi-step work, state a brief plan with verification attached to each step:

```text
1. [Step] -> verify: [check]
2. [Step] -> verify: [check]
3. [Step] -> verify: [check]
```

Strong success criteria let the agent continue independently. Weak criteria such as "make it work" should be clarified or translated into observable checks.

## Completion Check

Before finishing:

- Check that the diff is narrow and directly tied to the request.
- Check that no speculative abstraction or unrelated cleanup slipped in.
- Report what was verified and what remains unverified.
- If the best answer is to ask a clarifying question or push back, do that before editing.
