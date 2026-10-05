# Install prompt — Devin CLI / Windsurf

Paste the block below into a Devin session. It assumes the current directory is
this repo clone; if not, the agent clones it first.

---

Install the Devin port of SuperClaude from this repo (`devin/`) into my Devin
global skills directory.

Steps:
1. If the current directory is not the SuperClaude_Framework clone (check for
   `devin/skills/` and `devin/import-manifest.json`), run
   `git clone --depth 1 https://github.com/rebots-online/SuperClaude_Framework.git`
   in a scratch dir and work from there.
2. Resolve the Devin skills dir: `%APPDATA%\devin\skills` on Windows
   (typically `C:\Users\<me>\AppData\Roaming\devin\skills`) or
   `~/.config/devin/skills` on macOS/Linux. Create it if missing.
3. Copy `devin/skills/*` into that dir (63 skill dirs, each with SKILL.md),
   and copy `devin/superclaude-import/` there too — it adds the
   `/superclaude-import` updater skill.
4. Vendor the reference tree: copy `plugins/superclaude/` to
   `<devin-config>/superclaude/plugin/` (next to `skills/`) so imported skill
   bodies can resolve `core/`, `modes/`, `scripts/` docs.
5. For project scope instead, use `.devin/skills/` in the current repo (and
   skip step 4 unless bodies reference the vendor path).
6. Verify: list the installed `sc-*` skill dirs and confirm counts (30
   commands, 19 agents, 7 modes, 6 skills + 3 `-command` collision variants
   + `sc`).
7. Ask me whether to register the bundled MCP servers; if yes run
   `devin mcp add context7 --scope user -- npx -y @upstash/context7-mcp@latest`
   and `devin mcp add sequential-thinking --scope user -- npx -y @modelcontextprotocol/server-sequential-thinking`
   (needs `devin` CLI on PATH; otherwise print the commands for me).
8. Tell me they appear under `/` in the next session or after
   running /skills reload.

---
