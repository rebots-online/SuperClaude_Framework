---
name: sc-token-efficiency
description: Activate ultra-compressed output mode for maximum token efficiency. Use when context is running low, user requests brevity, or dealing with large-scale operations.
---

<!-- Ported from SuperClaude Framework (SuperClaude-Org/SuperClaude_Framework@206c7f8)
     Source: plugins/superclaude/skills/token-efficiency/SKILL.md
     Supporting files: ${ZCODE_PLUGIN_ROOT} (core/, modes/, scripts/, ...)
-->

# Token Efficiency Mode

Minimize token usage while preserving information quality (>=95%).

## Rules

- Use bullet points and tables, never verbose paragraphs
- Abbreviate common terms (fn=function, impl=implementation, cfg=config)
- Use symbols for status: OK, FAIL, WARN, SKIP
- One sentence per concept
- Code blocks only — no prose explanations of code
- Skip preamble, greetings, and transitions
- Target: 30-50% token reduction vs normal output
