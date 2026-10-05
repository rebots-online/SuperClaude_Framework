# Install prompt — ZCode (GLM-5.x)

Paste the block below into a ZCode Agent task. It assumes the current workspace
is this repo clone; if not, the agent clones it first.

---

Install the ZCode port of SuperClaude from this repo (`zcode/superclaude/`)
into my ZCode user configuration.

Steps:
1. If the current workspace is not the SuperClaude_Framework clone (check for
   `zcode/superclaude/.zcode-plugin/plugin.json`), clone
   `https://github.com/rebots-online/SuperClaude_Framework.git` into a scratch
   dir and work from there.
2. Copy, creating dirs as needed:
   - `zcode/superclaude/commands/*.md` → `~/.zcode/commands/`
   - `zcode/superclaude/skills/*` → `~/.zcode/skills/`
   - `zcode/superclaude/agents/*.md` → `~/.zcode/agents/`
   (honor `%ZCODE_HOME%`/`$ZCODE_HOME` if set)
3. Verify: count installed files (30 commands, 13 skills, 19 agents) and show me
   a few `/sc-*` command names.
4. Then explain the better path: this same repo is a ZCode marketplace — in
   Settings → Plugins → Create → Add marketplace I can add
   `rebots-online/SuperClaude_Framework` (or this local folder) and install the
   `superclaude` plugin, which additionally wires `hooks/hooks.json` and
   `.mcp.json` (context7 + sequential-thinking) and gives one-click
   enable/disable. Ask whether to keep or remove the direct copies if I take
   the plugin route (duplicate names can coexist, but cleaner to pick one).
5. Remind me components appear in the `/` panel and `$` skills on the next task.

---
