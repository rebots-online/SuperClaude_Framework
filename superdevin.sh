#!/usr/bin/env bash
# superdevin.sh - install SuperClaude port for Devin CLI / Windsurf
set -e
SRC="$(cd "$(dirname "$0")" && pwd)/devin"
DST="${XDG_CONFIG_HOME:-$HOME/.config}/devin/skills"

[ -d "$SRC/skills" ] || { echo "rendered skills missing: $SRC/skills" >&2; exit 1; }

echo "Copying skills to $DST"
mkdir -p "$DST"
cp -r "$SRC/skills/"* "$DST/"
cp -r "$SRC/superclaude-import" "$DST/superclaude-import"
echo "Installed: 63 /sc-* skills + superclaude-import (/superclaude-import)."

# vendor plugin tree so imported bodies can resolve supporting files
mkdir -p "${XDG_CONFIG_HOME:-$HOME/.config}/devin/superclaude"
cp -r "$(cd "$(dirname "$0")" && pwd)/plugins/superclaude" \
      "${XDG_CONFIG_HOME:-$HOME/.config}/devin/superclaude/plugin"
echo "Vendored reference tree -> ${XDG_CONFIG_HOME:-$HOME/.config}/devin/superclaude/plugin"

echo
echo "Project scope instead: cp -r devin/skills/* .devin/skills/"
echo "Restart Devin session (or /skills) for new entries to appear."
