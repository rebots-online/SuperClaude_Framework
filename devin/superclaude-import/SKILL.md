---
name: superclaude-import
description: Import SuperClaude framework components (skills, /sc:* commands, agents, modes) from github.com/SuperClaude-Org/SuperClaude_Framework into Devin-native skills. Use when the user says "import superclaude", "/superclaude-import", asks to install/update SuperClaude skills or commands, or wants /sc-* workflows in Devin.
argument-hint: "[skills|commands|agents|modes|all] [--project] [--list] [--dry-run] [--force] [--ref <ref>]"
allowed-tools:
  - exec
  - read
  - write
  - grep
  - glob
---

# superclaude-import

Imports the SuperClaude framework into Devin's native skill system — the Devin
equivalent of SuperClaude's own `install-skill` / plugin install, but targeting
Devin's skills directory instead of `~/.claude`.

## What it maps

Source: `plugins/superclaude/` inside `SuperClaude-Org/SuperClaude_Framework`.

| SuperClaude component | Installed as (Devin) |
|---|---|
| `skills/<name>/SKILL.md` (6 upstream) | `/sc-<name>` skill |
| `commands/<name>.md` (30, the `/sc:*` commands) | `/sc-<name>` skill |
| `agents/<name>.md` (19 personas) | `/sc-agent-<name>` skill with `subagent: true` |
| `modes/MODE_<Name>.md` (7) | `/sc-mode-<name>` skill |

Name collisions between `skills/` and `commands/` (upstream ships brainstorm,
pm, troubleshoot in both) resolve in favor of the skill — the command variant
installs as `/sc-<name>-command`.

Translation applied: `allowed-tools` names mapped to Devin tools
(`Read→read`, `Bash→exec`, `WebSearch→web_search`, `Task→run_subagent`,
`mcp__*` pass through), `context: fork` → `subagent: true`,
`disable-model-invocation` → `triggers: [user]`, `/sc:` → `/sc-`,
`~/.claude/` and `${CLAUDE_PLUGIN_ROOT}` → vendored plugin path.
`$ARGUMENTS`/`$1`–`$9` work natively in Devin skills and pass through.
Unmapped frontmatter (category, personas, mcp-servers…) is preserved as a
provenance comment in each imported file, not lost.

The whole plugin tree is also vendored to `<devin>/superclaude/plugin/` so
imported bodies can resolve references to `core/`, `modes/`, `mcp/`, etc.

## How to run

The importer is a stdlib-only Python script next to this file:

```bash
python "<this-skill-dir>/import_superclaude.py" --list          # inventory only
python "<this-skill-dir>/import_superclaude.py"                  # skills → global
python "<this-skill-dir>/import_superclaude.py" --components all # everything
python "<this-skill-dir>/import_superclaude.py" --components skills,commands
python "<this-skill-dir>/import_superclaude.py" --scope project  # ./.devin/skills
python "<this-skill-dir>/import_superclaude.py" --ref v4.1.0 --force  # pin+update
```

Resolve `<this-skill-dir>` from the skill's source path shown when this skill
loads (global: `%APPDATA%\devin\skills\superclaude-import`,
project: `.devin/skills/superclaude-import`).

Defaults: components=`skills`, scope=`global`, prefix=`sc-`, ref=`master`.
Install targets: global `%APPDATA%\devin\skills` (Win) / `~/.config/devin/skills`;
project `.devin/skills` in the current workspace root.

## Safety

- Idempotent: a manifest at `<devin>/superclaude/import-manifest.json` records
  what it installed; re-runs only overwrite importer-owned dirs. Pre-existing
  foreign skill dirs are skipped unless `--force`.
- `--dry-run` prints the plan without writing.
- `--repo-dir <path>` imports from a local clone (offline / audit flow).
- Third-party skills can carry prompt text that steers the agent — review
  vendored sources under `<devin>/superclaude/plugin/` if in doubt.

## After importing

Report what was installed and remind the user new skills show up in `/`
completions on the next session (or `/skills` reload). Imported MCP-dependent
bodies degrade gracefully per their own fallback text; the plugin's `.mcp.json`
is vendored but NOT auto-installed — offer `devin mcp add` only if asked.

## Updating / uninstalling

- Update: rerun with `--force` (overwrites only importer-owned dirs) and a
  newer `--ref`.
- Uninstall: delete the `sc-*` dirs listed in the manifest and the
  `<devin>/superclaude/` vendor dir.
