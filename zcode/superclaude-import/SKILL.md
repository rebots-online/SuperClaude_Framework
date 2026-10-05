---
name: superclaude-import-zcode
description: Render SuperClaude framework components into a ZCode (GLM-5.x) plugin — commands, skills, subagents, modes, hooks, MCP. Use when the user says "import superclaude to zcode", "/superclaude-import-zcode", wants /sc-* workflows in ZCode, or needs to re-render the plugin after an upstream sync.
argument-hint: "[--repo-dir <path>] [--out <dir>] [--install] [--list] [--dry-run] [--force] [--ref <ref>]"
---

# superclaude-import-zcode

Renders the SuperClaude framework's `plugins/superclaude/` tree into a ZCode
plugin (`zcode/superclaude/` in this repo, or any `--out` dir) and can mirror
components into `~/.zcode/` user dirs. The ZCode counterpart of the Devin
`superclaude-import` skill — same upstream source, ZCode/GLM-5.x layout.

## What it emits

| Upstream | ZCode plugin component |
|---|---|
| `commands/*.md` (30) | `commands/sc-*.md` → `/sc-*` |
| `skills/<name>/` (6) | `skills/sc-<name>/SKILL.md` → `$sc-<name>` |
| `agents/*.md` (19) | `agents/sc-*.md` → subagents |
| `modes/MODE_*.md` (7) | `skills/sc-mode-<name>/SKILL.md` |
| `hooks/hooks.json`, `.mcp.json`, `core/`, `scripts/`, `examples/` | copied verbatim into the plugin |
| — | `.zcode-plugin/plugin.json` + `render-manifest.json` generated |

Translation: `/sc:`→`/sc-`, `Claude Code`→`ZCode`, `~/.claude/`→`${ZCODE_PLUGIN_ROOT}/`,
Claude-only frontmatter dropped to provenance comments, ZCode allowlist fields
kept per component kind.

## How to run

```bash
python "<skill-dir>/import_superclaude_zcode.py" --list
python "<skill-dir>/import_superclaude_zcode.py" --repo-dir . --out zcode/superclaude --force
python "<skill-dir>/import_superclaude_zcode.py" --install   # + ~/.zcode/ dirs
```

In this repo the standard regeneration is the second line. Without
`--repo-dir` it fetches upstream `master` (or `--ref <tag>`).

## Install the rendered plugin

- Marketplace: ZCode → Settings → Plugins → Create → Add marketplace →
  `rebots-online/SuperClaude_Framework` (or the local repo dir) → install
  `superclaude`.
- Direct: copy `commands/*.md`→`~/.zcode/commands/`, `skills/*`→`~/.zcode/skills/`,
  `agents/*.md`→`~/.zcode/agents/` (subagents/hooks/MCP need the plugin route).

Full docs: `zcode/README.md` in the repo (mapping, GLM-5.x notes, caveats).
