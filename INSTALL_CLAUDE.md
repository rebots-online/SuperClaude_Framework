# Install prompt — Claude Code

Paste the block below into a Claude Code session. It assumes the current
directory is this repo clone; if not, the agent clones it first.

---

Install the SuperClaude framework from this repo into `~/.claude` for Claude Code.

Steps:
1. If the current directory is not the SuperClaude_Framework clone (check for
   `plugins/superclaude/commands/`), run
   `git clone --depth 1 https://github.com/rebots-online/SuperClaude_Framework.git`
   in a scratch dir and work from there.
2. Copy from this clone (NOT the PyPI package):
   - `plugins/superclaude/commands/*.md` → `~/.claude/commands/sc/`
   - `plugins/superclaude/agents/*.md` → `~/.claude/agents/`
   - `plugins/superclaude/skills/*` → `~/.claude/skills/`
   - `plugins/superclaude/modes/*.md` and `plugins/superclaude/core/*.md` → `~/.claude/`
   Do not overwrite `~/.claude/CLAUDE.md` or `settings.json` if present.
   (If I say I prefer the official package, you may instead run
   `pipx install superclaude && superclaude install` — but default to the copy.)
3. Verify: count files installed (expect ~30 commands, ~19 agents, 6+ skills)
   and list a few of each.
4. Tell me to restart Claude Code; `/sc:*` commands and `@` agents activate on
   the next session. Mention that `.mcp.json`/hooks were not wired and can be
   configured in settings if wanted.

---
