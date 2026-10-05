#!/usr/bin/env bash
# superclaude.sh - install SuperClaude for Claude Code from THIS clone
# (no PyPI/pipx; copies the vendored plugins/superclaude tree)
# If you prefer the official package instead: pipx install superclaude && superclaude install
set -e
SRC="$(cd "$(dirname "$0")" && pwd)/plugins/superclaude"
DST="$HOME/.claude"

[ -d "$SRC/commands" ] || { echo "plugin tree missing: $SRC" >&2; exit 1; }

echo "Copying components to $DST"
mkdir -p "$DST/commands/sc" "$DST/agents" "$DST/skills"
cp "$SRC/commands/"*.md "$DST/commands/sc/"
cp "$SRC/agents/"*.md "$DST/agents/"
cp -r "$SRC/skills/"* "$DST/skills/"
cp "$SRC/modes/"*.md "$SRC/core/"*.md "$DST/" 2>/dev/null || true
echo "Installed: commands->commands/sc (/sc:*), agents, skills, modes+core docs."
echo
echo "Not wired (official installer handles these): .mcp.json, hooks, CLAUDE.md imports."
echo "Configure in Claude Code settings if wanted."
echo "Restart Claude Code to pick up /sc:* commands."
