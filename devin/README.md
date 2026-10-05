# SuperClaude for Devin CLI / Windsurf

This directory is the Devin-native distribution of SuperClaude. Everything in
`plugins/superclaude/` — 30 `/sc:*` commands, 19 agent personas, 7 behavioral
modes, 6 skills — is ported to Devin `SKILL.md` format and invocable as
`/sc-*` slash commands.

Upstream: [`SuperClaude-Org/SuperClaude_Framework`](https://github.com/SuperClaude-Org/SuperClaude_Framework)
(forked at `master@fe68862`).

## Layout

```
devin/
├── superclaude-import/        # Devin skill: fetches + translates upstream
│   ├── SKILL.md               #   (install this one first if you want updates)
│   └── import_superclaude.py  # stdlib-only importer (Python 3.10+)
├── skills/                    # 63 pre-rendered Devin skills — copy and use
│   ├── sc-implement/SKILL.md
│   ├── sc-agent-system-architect/SKILL.md
│   ├── sc-mode-brainstorming/SKILL.md
│   └── ...
└── import-manifest.json       # provenance: upstream commit, item list
```

## Install

**Copy the pre-rendered skills** (no Python needed):

```bash
# Windows
xcopy /E /I devin\skills\* "%APPDATA%\devin\skills\"

# macOS / Linux
cp -r devin/skills/* ~/.config/devin/skills/
```

Or install per-project by copying into `<repo>/.devin/skills/` instead —
that commits them to git for the whole team.

**Or run the importer** (fetches latest upstream, translates, installs):

```bash
python devin/superclaude-import/import_superclaude.py --components all
python devin/superclaude-import/import_superclaude.py --list      # inventory
python devin/superclaude-import/import_superclaude.py --scope project
```

Or simply install `devin/superclaude-import/` as a skill and ask Devin to
`/superclaude-import all`.

## What the port does

| Upstream (`plugins/superclaude/`) | Devin skill |
|---|---|
| `commands/<name>.md` | `/sc-<name>` |
| `skills/<name>/` | `/sc-<name>` |
| `agents/<name>.md` | `/sc-agent-<name>` (`subagent: true`) |
| `modes/MODE_<Name>.md` | `/sc-mode-<name>` |

- `allowed-tools` translated to Devin tool names (`Bash`→`exec`,
  `Task`→`run_subagent`, `WebSearch`→`web_search`, `mcp__*` passthrough)
- `context: fork` → `subagent: true`; `disable-model-invocation` → `triggers: [user]`
- `/sc:` references rewritten to `/sc-`; `~/.claude/` and `${CLAUDE_PLUGIN_ROOT}`
  rewritten to the vendored/referenced plugin path
- `$ARGUMENTS` / `$1`–`$9` work natively in Devin and pass through unchanged
- Unmapped frontmatter (`personas`, `mcp-servers`, `category`, `complexity`)
  is preserved in a provenance comment at the top of each file
- `skills/` vs `commands/` name collisions (brainstorm, pm, troubleshoot):
  the skill wins `/sc-<name>`; the command becomes `/sc-<name>-command`

## Caveats

- MCP-dependent bodies (Context7, Tavily, Sequential, Magic, Playwright)
  degrade gracefully per their own fallback text. The plugin's `.mcp.json`
  is **not** auto-installed — use `devin mcp add` for the ones you want.
- Hooks (`hooks/hooks.json`) and `core/` rule files are referenced, not
  activated; wire them into `.devin/config.json` / `AGENTS.md` manually.
- Third-party skill bodies are prompt text — review before enabling
  model-triggered ones.

## Syncing from upstream

```bash
git fetch upstream
git merge upstream/master            # or rebase; keep devin/ tree
python devin/superclaude-import/import_superclaude.py \
  --repo-dir . --components all \
  --skills-dir devin/skills --vendor-link plugins/superclaude
git commit -am "chore(devin): re-render skills from upstream <sha>"
```
