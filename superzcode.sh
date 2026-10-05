#!/usr/bin/env bash
# superzcode.sh - install SuperClaude port for ZCode (GLM-5.x)
set -e
SRC="$(cd "$(dirname "$0")" && pwd)/zcode/superclaude"
DST="${ZCODE_HOME:-$HOME/.zcode}"

[ -d "$SRC/commands" ] || { echo "rendered plugin missing: $SRC" >&2; exit 1; }

echo "Copying components to $DST (user scope)"
mkdir -p "$DST/commands" "$DST/skills" "$DST/agents"
cp "$SRC/commands/"*.md "$DST/commands/"
cp -r "$SRC/skills/"* "$DST/skills/"
cp "$SRC/agents/"*.md "$DST/agents/"
echo "Installed: 30 commands (/sc-*), 13 skills (\$sc-*), 19 subagents."
echo
echo "For hooks + MCP servers + one-click enable/disable, install as a plugin instead:"
echo "  ZCode -> Settings -> Plugins -> Create -> Add marketplace"
echo "  -> rebots-online/SuperClaude_Framework  (or this local folder)"
echo "  -> Install 'superclaude'"
echo
echo "Restart ZCode (new task) to pick up components."
