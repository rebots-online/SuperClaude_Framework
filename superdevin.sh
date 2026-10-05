#!/usr/bin/env bash
# superdevin.sh - install SuperClaude port for Devin CLI / Windsurf
set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"
SRC="$ROOT/devin"
DEVIN_CFG="${XDG_CONFIG_HOME:-$HOME/.config}/devin"
DST="$DEVIN_CFG/skills"

[ -d "$SRC/skills" ] || { echo "rendered skills missing: $SRC/skills" >&2; exit 1; }

echo "Copying skills to $DST"
mkdir -p "$DST"
cp -r "$SRC/skills/"* "$DST/"
cp -r "$SRC/superclaude-import" "$DST/superclaude-import"
echo "Installed: 63 /sc-* skills + superclaude-import (/superclaude-import)."

# vendor plugin tree so imported bodies can resolve supporting files
mkdir -p "$DEVIN_CFG/superclaude"
cp -r "$ROOT/plugins/superclaude" "$DEVIN_CFG/superclaude/plugin"
echo "Vendored reference tree -> $DEVIN_CFG/superclaude/plugin"
echo

if [ -t 0 ] && command -v devin >/dev/null 2>&1; then
    read -r -p "Register context7 + sequential-thinking MCP via 'devin mcp add' (user scope)? [y/N] " a
    case "$a" in
        y|Y)
            devin mcp add context7 --scope user -- npx -y @upstash/context7-mcp@latest || true
            devin mcp add sequential-thinking --scope user -- npx -y @modelcontextprotocol/server-sequential-thinking || true
            ;;
    esac
elif ! command -v devin >/dev/null 2>&1; then
    echo "(devin CLI not found - skipping optional MCP registration)"
    echo "  To add later: devin mcp add context7 --scope user -- npx -y @upstash/context7-mcp@latest"
    echo "                devin mcp add sequential-thinking --scope user -- npx -y @modelcontextprotocol/server-sequential-thinking"
fi

echo
echo "Project scope instead: cp -r devin/skills/* .devin/skills/"
echo "Restart Devin session (or /skills) for new entries to appear."
