#!/usr/bin/env bash
# superclaude.sh - install SuperClaude for Claude Code (upstream target)
set -e
SRC="$(cd "$(dirname "$0")" && pwd)/plugins/superclaude"
DST="$HOME/.claude"

if command -v superclaude >/dev/null 2>&1; then
    echo "Using official installer: superclaude install"
    exec superclaude install "$@"
elif command -v pipx >/dev/null 2>&1; then
    echo "Installing via pipx, then superclaude install"
    pipx install superclaude && exec superclaude install "$@"
fi

echo "superclaude CLI not found - falling back to direct copy into $DST"
[ -d "$SRC" ] || { echo "plugin tree missing: $SRC" >&2; exit 1; }
mkdir -p "$DST/commands/sc" "$DST/agents" "$DST/skills"
cp -r "$SRC/commands/"* "$DST/commands/sc/"
cp -r "$SRC/agents/"* "$DST/agents/"
cp -r "$SRC/skills/"* "$DST/skills/" 2>/dev/null || true
cp "$SRC/modes/"*.md "$SRC/core/"*.md "$DST/" 2>/dev/null || true
echo "Copied commands->commands/sc, agents, skills, modes+core docs to $DST"
echo "Note: .mcp.json and hooks not wired - configure in Claude Code settings if wanted."
echo "Restart Claude Code to pick up /sc:* commands."
