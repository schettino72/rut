---
layout: default
title: "Why Unit Tests Matter More for AI Coding Than for Humans"
---

An AI coding agent doesn't remember what it broke three iterations ago. Your test suite does.

## The agent loop

AI coding agents work by looping:

```
Prompt → Plan → Code → Run Tests → [fail? loop back] → Manual Verify → Commit
```

The agent writes code, runs tests, sees failures, fixes them, and repeats. This loop is where the magic happens — or doesn't.

## Why verification matters

Without automated tests in the loop, agents generate slop. Three reasons:

**1. Agents make mistakes constantly.**
They hallucinate APIs, forget context, introduce subtle bugs. Unlike a human who might catch their own typo, an agent will confidently produce broken code. Tests catch these immediately.

**2. Agents can't hold everything in memory.**
On iteration 5, the agent doesn't remember what it broke in iteration 2. The context window is finite. Your test suite isn't — it remembers every constraint you encoded.

**3. Regressions are the silent killer.**
The agent fixes bug A and reintroduces bug B. Without tests, you won't know until production. With tests, you know in seconds.

## Tests as a reasoning step

Here's something less obvious: asking an agent to write tests first often produces better code.

This is similar to chain-of-thought prompting. When you ask an LLM to reason through steps instead of jumping to an answer, quality improves. Writing tests forces the agent to think about:

- What should this code actually do?
- What are the edge cases?
- What does success look like?

The tests become a specification. The agent then writes code to match that specification. It's TDD, but the benefit isn't just "tests exist" — it's that the planning step improves the implementation.

## Humans vs agents

When a human runs a slow test suite, they context-switch. Check email. Read docs. Think about the problem. The wait doesn't feel like pure waste.

An agent doesn't context-switch. It waits. And if your test suite takes 3 minutes, and the agent needs 5 iterations, that's 15 minutes of wall-clock time. The feedback loop stretches until it breaks.

Fast tests aren't just nice-to-have. They're what keeps the agent loop tight enough to be useful.

## What good looks like

- Tests that run in seconds, not minutes
- Tests that catch regressions automatically
- Clean architecture so you can run *only* affected tests
- A workflow where the agent runs tests on every iteration

If you're using AI coding tools and your test suite is slow or flaky or nonexistent, you're leaving most of the value on the table.

The agent loop only works if there's something to loop against.

---

*If you're interested in running only affected tests to speed up the loop, I've been working on this problem since 2008. More on that soon.*
