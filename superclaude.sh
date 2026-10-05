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
cp "$SRC/modes/"*.md "$SRC/core/"*.md "$SRC/mcp/"*.md "$DST/" 2>/dev/null || true
echo "Installed: commands->commands/sc (/sc:*), agents, skills, modes+core+mcp docs."
echo

if [ -t 0 ] && command -v claude >/dev/null 2>&1; then
    read -r -p "Register context7 + sequential-thinking MCP servers via 'claude mcp add'? [y/N] " a
    case "$a" in
        y|Y)
            claude mcp add context7 -- npx -y @upstash/context7-mcp@latest || true
            claude mcp add sequential-thinking -- npx -y @modelcontextprotocol/server-sequential-thinking || true
            ;;
    esac
elif ! command -v claude >/dev/null 2>&1; then
    echo "(claude CLI not found - skipping optional MCP registration)"
    echo "  To add later: claude mcp add context7 -- npx -y @upstash/context7-mcp@latest"
    echo "                claude mcp add sequential-thinking -- npx -y @modelcontextprotocol/server-sequential-thinking"
fi

echo "Hooks (opt-in): merge $SRC/hooks/hooks.json into ~/.claude/settings.json \"hooks\" section."
echo "Restart Claude Code to pick up /sc:* commands."
