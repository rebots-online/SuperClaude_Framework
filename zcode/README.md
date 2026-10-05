# SuperClaude for ZCode / GLM-5.x

This directory is the ZCode-native distribution of SuperClaude, tailored for
Z.ai's ZCode ADE running the GLM-5.x model family (GLM-5.3 tuned, 1M stable
context, long-horizon tasks, Goal Mode, execution modes, `$` skills,
`/` commands, `@` file refs, `#` conversation links, subagents, plugins, MCP).

Upstream: [`SuperClaude-Org/SuperClaude_Framework`](https://github.com/SuperClaude-Org/SuperClaude_Framework)
(rendered from `plugins/superclaude/` @ upstream `master`).

## Layout

```
zcode/
├── README.md                      # this file
├── import_superclaude_zcode.py    # customized renderer (stdlib-only Python 3.10+)
├── superclaude-import/            # the importer packaged as a skill
│   ├── SKILL.md
│   └── import_superclaude_zcode.py
└── superclaude/                   # THE ZCode plugin (ready to install)
    ├── .zcode-plugin/plugin.json  # manifest
    ├── commands/sc-*.md           # 30 commands -> /sc-implement etc.
    ├── skills/sc-*/SKILL.md       # 6 skills + 7 modes (sc-mode-*)
    ├── agents/sc-*.md             # 19 persona subagents
    ├── hooks/hooks.json           # verbatim (${CLAUDE_PLUGIN_ROOT} works)
    ├── .mcp.json                  # verbatim (context7, sequential-thinking)
    ├── core/ modes/ scripts/ examples/  # reference docs copied verbatim
    └── render-manifest.json       # provenance: upstream commit, item list
```

## Install — marketplace (recommended)

The fork itself is a ZCode marketplace:

1. ZCode → **Settings → Plugins → Create → Add marketplace**
2. Enter `rebots-online/SuperClaude_Framework` (or the repo URL)
3. Find **superclaude** under Personal → **Install**

The plugin registers commands, skills, subagents, hooks, and both MCP servers
in one shot. Disable/enable together from Manage installed.

Local testing without GitHub: **Add marketplace** → choose this repo's local
directory (root `marketplace.json` resolves `./zcode/superclaude`).

## Install — direct copy (no plugin system)

```bash
# Windows (Git Bash) / macOS / Linux
cp zcode/superclaude/commands/*.md ~/.zcode/commands/
cp -r zcode/superclaude/skills/* ~/.zcode/skills/
cp zcode/superclaude/agents/*.md ~/.zcode/agents/
```

Plugin install is preferred: subagents/hooks/MCP only register through it.

## Regenerate after upstream sync

```bash
python zcode/import_superclaude_zcode.py --repo-dir . --out zcode/superclaude --force
```

`--install` additionally mirrors commands/skills/agents into `~/.zcode/`.
`--list` / `--dry-run` inspect without writing. No `--repo-dir` → fetches
upstream `master` (or `--ref <tag>`).

## Translation rules

- `commands/*.md` → `commands/sc-*.md`; `/sc:` → `/sc-` in bodies
- `skills/<name>/` → `skills/sc-<name>/SKILL.md` (sibling files copied)
- `agents/*.md` → `agents/sc-*.md` (native subagents, auto-dispatch by description)
- `modes/MODE_*.md` → `skills/sc-mode-<name>/SKILL.md` (ZCode has no modes)
- frontmatter filtered to ZCode's allowlist per kind (commands:
  `description, argument-hint, allowed-tools, model, skills,
  disable-noninteractive`; skills: `name, description, when_to_use, license,
  metadata`; agents: `name, description`); dropped fields preserved in the
  provenance comment of each file
- `Claude Code` → `ZCode` in prose; `~/.claude/` → `${ZCODE_PLUGIN_ROOT}/`
- `disable-model-invocation` / Claude model ids dropped (GLM-5.x doesn't take them)
- `$ARGUMENTS` / `$1`–`$9` — supported natively, pass through

## GLM-5.x tailoring notes

SuperClaude was designed around Claude Code's primitives; several of its
components now overlap with ZCode/GLM-5.3 native features. Use the native
feature when both exist:

| SuperClaude component | ZCode / GLM-5.x native equivalent |
|---|---|
| `MODE_Task_Management` (`sc-mode-task-management`) | **Goal Mode** (`/goal` builtin) + Memory + task list |
| `MODE_Introspection` | GLM-5.3 **thought levels** (model reasoning control) |
| `MODE_Token_Efficiency` | 1M context makes this less critical — still useful for quota/latency; `/compact` builtin |
| `/sc-save`, `/sc-load` (session persistence) | `#` conversation links, **Memory**, Edit History |
| `/sc-spawn` (parallel tasks) | ZCode **Subagents** (auto-dispatch) + Remote/Bot Channel |
| `/sc-pm` (PDCA, context restore) | Goal Mode + Memory cover most of it |
| `hooks` SessionStart/Stop | ZCode hooks events (SessionStart, Stop, PostToolUse…) — same schema |
| `confidence-check` skill | works as-is — `$sc-confidence-check` |

GLM-5.x strengths to lean on: stable 1M context (long spec/design docs can go
in the prompt rather than being summarized away), long-horizon task execution
(pair `/sc-task` with Goal Mode), GLM-5.3-Flash for multimodal/screenshot
steps.

## Caveats

- `hooks/hooks.json` SessionStart runs `scripts/session-init.sh` — a POSIX
  shell script; on Windows it needs Git Bash/WSL or it will silently fail.
  The `prompt`-type hooks (Stop/PostToolUse) are shell-free and work anywhere.
- `.mcp.json` ships `context7` + `sequential-thinking` via `npx` (needs Node).
  Other SuperClaude MCP servers (Tavily, Magic, Playwright, Serena, Morphllm)
  are documented upstream — add under **Settings → MCP** if wanted.
- Same-name coexistence is intended: `/sc-brainstorm` (command) and
  `$sc-brainstorm` (skill) are different triggers in ZCode — no collision.
- Commands are prompt text steering the agent — review `core/`, `commands/`
  sources before trusting them in privileged workspaces.
