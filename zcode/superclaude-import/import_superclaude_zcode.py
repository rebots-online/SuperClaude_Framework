#!/usr/bin/env python3
"""
import_superclaude_zcode.py - render SuperClaude framework components as a
ZCode (GLM-5.x) plugin, and optionally install components into ~/.zcode.

Fetches SuperClaude-Org/SuperClaude_Framework (the plugins/superclaude tree)
or reads a local clone, translates Claude Code conventions into ZCode format,
and emits an installable ZCode plugin:

    <out>/
      .zcode-plugin/plugin.json
      commands/sc-*.md          (30 /sc:* commands -> /sc-* commands)
      skills/sc-*/SKILL.md      (6 skills + 7 modes as sc-mode-*)
      agents/sc-*.md            (19 persona subagents)
      hooks/hooks.json          (verbatim; ${CLAUDE_PLUGIN_ROOT} works in ZCode)
      .mcp.json                 (verbatim: context7 + sequential-thinking)
      core/ modes/ scripts/ examples/   (reference dirs, copied verbatim)

Stdlib only. Windows/macOS/Linux.

Examples:
  python import_superclaude_zcode.py --list
  python import_superclaude_zcode.py --repo-dir . --out zcode/superclaude
  python import_superclaude_zcode.py --install   # also copy into ~/.zcode/
"""

import argparse
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO = "SuperClaude-Org/SuperClaude_Framework"
DEFAULT_REF = "master"
PLUGIN_SUBDIR = Path("plugins") / "superclaude"

# upstream component dir -> (kind, plugin subdir or None)
COMPONENTS = {
    "commands": ("commands", "commands"),   # *.md -> commands/sc-*.md
    "skills": ("skills", "skills"),         # <name>/SKILL.md -> skills/sc-<name>/
    "agents": ("agents", "agents"),         # *.md -> agents/sc-*.md
    "modes": ("modes", "skills"),           # MODE_*.md -> skills/sc-mode-<name>/
}
# non-component dirs copied verbatim into the plugin for reference/hooks
PASSTHROUGH_DIRS = ["core", "modes", "scripts", "examples", "mcp"]
PASSTHROUGH_FILES = [".mcp.json", "hooks/hooks.json", "README.md"]

# fields ZCode understands, per component kind (docs: plugin -> field reference)
ZCODE_FIELDS = {
    "commands": {"description", "argument-hint", "allowed-tools", "model",
                 "skills", "disable-noninteractive"},
    "skills": {"name", "description", "when_to_use", "license", "metadata"},
    "agents": {"name", "description"},
    "modes": {"name", "description", "when_to_use", "license", "metadata"},
}
# Claude model ids that mean nothing to ZCode/GLM -> drop
DROP_MODELS = {"inherit", "haiku", "sonnet", "opus"}


class RawBlock(str):
    pass


# ---------------------------------------------------------------- frontmatter

def _scalar(v):
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        v = v[1:-1]
    if v.lower() in ("true", "false"):
        return v.lower() == "true"
    return v


def parse_frontmatter(text):
    text = text.replace("\r\n", "\n")
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", text, re.S)
    if not m:
        return {}, text
    raw, body = m.group(1), m.group(2)
    fm, key = {}, None
    for line in raw.split("\n"):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(line) - len(line.lstrip())
        mm = re.match(r"^([A-Za-z0-9_-]+)\s*:\s*(.*)$", line.lstrip())
        if mm and indent == 0:
            key = mm.group(1)
            val = mm.group(2).strip()
            if val == "":
                fm[key] = []
            elif val.startswith("[") and val.endswith("]"):
                fm[key] = [_scalar(x) for x in val[1:-1].split(",") if x.strip()]
            else:
                fm[key] = _scalar(val)
        elif indent > 0 and key is not None and isinstance(fm.get(key), list):
            if stripped.startswith("- "):
                fm[key].append(_scalar(stripped[2:]))
            else:
                if not isinstance(fm[key], RawBlock):
                    fm[key] = RawBlock(key)
                fm[key] = RawBlock((fm[key] + "\n" + line).lstrip("\n"))
    for k, v in list(fm.items()):
        if isinstance(v, list) and not v:
            fm[k] = None
    return fm, body


def _emit_scalar(v):
    s = str(v)
    if re.search(r"[:#\[\]{}\n]|^[\"']|[\"']$|^\s|\s$", s):
        return json.dumps(s)
    return s


def dump_frontmatter(fm):
    out = ["---"]
    for k, v in fm.items():
        if v is None:
            continue
        if isinstance(v, RawBlock):
            out.append(f"{k}:")
            out.extend(v.split("\n"))
        elif isinstance(v, list):
            # ZCode commands take comma-separated allowed-tools
            if k == "allowed-tools":
                out.append(f"{k}: {', '.join(str(i) for i in v)}")
            else:
                out.append(f"{k}:")
                out += [f"  - {_emit_scalar(i)}" for i in v]
        elif isinstance(v, bool):
            out.append(f"{k}: {'true' if v else 'false'}")
        else:
            out.append(f"{k}: {_emit_scalar(v)}")
    out.append("---")
    return "\n".join(out)


# ------------------------------------------------------------- translation

def slugify(name):
    s = re.sub(r"[^a-zA-Z0-9]+", "-", name).strip("-").lower()
    return s or "unnamed"


def out_name(kind, src_name):
    """Component name inside the ZCode plugin (sc- prefixed)."""
    if kind == "modes":
        base = f"mode-{slugify(src_name)}"
    else:
        base = slugify(src_name)
    if kind == "commands" and base == "sc":
        return "sc"  # /sc stays the namespace index
    return f"sc-{base}"


def convert_file(text, *, kind, name, src_rel, sha):
    """Translate one source .md to ZCode frontmatter+body. Returns (fm, text)."""
    fm, body = parse_frontmatter(text)
    notes = []

    keep = ZCODE_FIELDS[kind]
    if isinstance(fm.get("model"), str) and fm["model"].strip().lower() in DROP_MODELS:
        fm.pop("model")
        notes.append("dropped Claude-only model field")
    if "allowed-tools" in fm and isinstance(fm["allowed-tools"], str):
        fm["allowed-tools"] = [t.strip() for t in fm["allowed-tools"].split(",")]
    if fm.get("disable-model-invocation") is True:
        fm.pop("disable-model-invocation")
        notes.append("disable-model-invocation has no ZCode equivalent; dropped")

    extra = {k: v for k, v in fm.items() if k not in keep and v is not None}
    fm = {k: v for k, v in fm.items() if k in keep}
    if extra:
        rendered = ", ".join(
            f"{k}={v if not isinstance(v, RawBlock) else '<block>'}" for k, v in extra.items()
        )
        notes.append(f"unmapped fields: {rendered}")

    if kind != "commands":
        fm["name"] = name
    if not fm.get("description"):
        fm["description"] = f"SuperClaude {kind[:-1]}: {name}"

    # body adaptation
    body = body.replace("/sc:", "/sc-")
    body = body.replace("${CLAUDE_PLUGIN_ROOT}", "${ZCODE_PLUGIN_ROOT}")
    body = body.replace("~/.claude/", "${ZCODE_PLUGIN_ROOT}/")
    body = body.replace("Claude Code", "ZCode")

    header = (
        f"<!-- Ported from SuperClaude Framework ({REPO}@{sha})\n"
        f"     Source: {src_rel}\n"
        f"     Supporting files: ${{ZCODE_PLUGIN_ROOT}} (core/, modes/, scripts/, ...)\n"
    )
    if notes:
        header += "     Port notes: " + "; ".join(notes) + "\n"
    header += "-->\n\n"
    return fm, dump_frontmatter(fm) + "\n\n" + header + body


# ------------------------------------------------------------------- source

def fetch_source(ref, repo_dir):
    if repo_dir:
        p = Path(repo_dir)
        if not (p / PLUGIN_SUBDIR).is_dir():
            sys.exit(f"--repo-dir {p} has no {PLUGIN_SUBDIR}")
        sha = "local"
        try:
            sha = subprocess.run(
                ["git", "-C", str(p), "rev-parse", "--short", "HEAD"],
                capture_output=True, text=True, timeout=15,
            ).stdout.strip() or "local"
        except Exception:
            pass
        return p, sha, None

    tmp = Path(tempfile.mkdtemp(prefix="superclaude-zcode-"))
    dest = tmp / "repo"
    try:
        subprocess.run(
            ["git", "clone", "--depth", "1", "--branch", ref,
             f"https://github.com/{REPO}.git", str(dest)],
            check=True, capture_output=True, text=True, timeout=300,
        )
        sha = subprocess.run(
            ["git", "-C", str(dest), "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True,
        ).stdout.strip()
        return dest, sha, tmp
    except Exception as e:
        print(f"git clone failed ({e}); falling back to tarball", file=sys.stderr)

    url = f"https://codeload.github.com/{REPO}/tar.gz/{ref}"
    with urllib.request.urlopen(url, timeout=120) as r:
        data = r.read()
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tf:
        tf.extractall(tmp / "tar")
    roots = list((tmp / "tar").iterdir())
    if len(roots) != 1:
        sys.exit("unexpected tarball layout")
    return roots[0], ref, tmp


# ------------------------------------------------------------------- render

def iter_items(plugin):
    """Yield (kind, src_name, md_path, siblings)."""
    for kind, (cdir_name, _dest) in COMPONENTS.items():
        cdir = plugin / cdir_name
        if not cdir.is_dir():
            print(f"warning: {cdir} missing, skipping {kind}", file=sys.stderr)
            continue
        if kind == "skills":
            for d in sorted(cdir.iterdir()):
                md = d / "SKILL.md"
                if d.is_dir() and md.is_file():
                    sib = [f for f in d.iterdir() if f.name != "SKILL.md" and f.is_file()]
                    yield kind, d.name, md, sib
        else:
            for f in sorted(cdir.glob("*.md")):
                stem = f.stem
                if kind == "modes":
                    stem = re.sub(r"^MODE_?", "", stem)
                yield kind, stem, f, []


def dest_path(out_root, kind, name):
    """Destination path for a component inside the ZCode plugin dir."""
    if kind == "skills" or kind == "modes":
        return out_root / "skills" / name / "SKILL.md"
    return out_root / COMPONENTS[kind][1] / f"{name}.md"


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--ref", default=DEFAULT_REF, help="upstream git ref (default master)")
    ap.add_argument("--repo-dir", help="use an existing local clone instead of fetching")
    ap.add_argument("--out", default=None,
                    help="plugin output dir (default: <repo-dir>/zcode/superclaude or ./zcode/superclaude)")
    ap.add_argument("--install", action="store_true",
                    help="also copy commands/skills/agents into the user-scope ~/.zcode dirs")
    ap.add_argument("--list", action="store_true", help="list components, write nothing")
    ap.add_argument("--dry-run", action="store_true", help="show planned writes, write nothing")
    ap.add_argument("--force", action="store_true", help="overwrite existing output dir content")
    args = ap.parse_args()

    repo_path, sha, tmp = fetch_source(args.ref, args.repo_dir)
    try:
        plugin = repo_path / PLUGIN_SUBDIR
        if not plugin.is_dir():
            sys.exit(f"plugin tree not found at {PLUGIN_SUBDIR} in {repo_path}")

        out_root = Path(args.out) if args.out else (
            (repo_path / "zcode" / "superclaude") if args.repo_dir
            else Path.cwd() / "zcode" / "superclaude")

        items = list(iter_items(plugin))
        if args.list:
            for kind, src, md, _sib in items:
                print(f"{kind:8} {src:28} -> {dest_path(Path('<out>'), kind, out_name(kind, src))}")
            print(f"\n{len(items)} item(s) from {REPO}@{sha}")
            return

        plan = []
        for kind, src, md, siblings in items:
            name = out_name(kind, src)
            plan.append((kind, src, md, siblings, name, dest_path(out_root, kind, name)))

        for kind, src, md, siblings, name, target in plan:
            print(f"  write {kind:8} {src:24} -> {target}")
        if args.dry_run:
            print(f"\ndry-run: {len(plan)} item(s), plugin out {out_root}")
            return

        if out_root.exists() and any(out_root.iterdir()) and not args.force:
            # allow idempotent re-render: our files are all sc-*/sc-* or manifest-owned
            marker = out_root / ".zcode-plugin" / "plugin.json"
            if not marker.exists():
                sys.exit(f"{out_root} exists and is not a prior render; use --force")

        for kind, src, md, siblings, name, target in plan:
            target.parent.mkdir(parents=True, exist_ok=True)
            src_rel = md.relative_to(repo_path).as_posix()
            _fm, content = convert_file(
                md.read_text(encoding="utf-8"), kind=kind, name=name,
                src_rel=src_rel, sha=sha)
            target.write_text(content, encoding="utf-8")
            for s in siblings:
                shutil.copy2(s, target.parent / s.name)

        # verbatim component-adjacent files
        for rel in PASSTHROUGH_FILES:
            src_f = plugin / rel
            if src_f.is_file():
                dst = out_root / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_f, dst)
        for d in PASSTHROUGH_DIRS:
            src_d = plugin / d
            if src_d.is_dir():
                shutil.copytree(src_d, out_root / d, dirs_exist_ok=True)

        # plugin manifest
        manifest = {
            "name": "superclaude",
            "version": "4.3.0",
            "description": "SuperClaude framework ported for ZCode/GLM-5.x — 30 commands, 19 subagents, 13 skills, hooks, MCP",
            "author": {"name": "rebots-online",
                       "url": "https://github.com/rebots-online/SuperClaude_Framework"},
            "homepage": "https://github.com/rebots-online/SuperClaude_Framework",
            "repository": "https://github.com/rebots-online/SuperClaude_Framework",
            "license": "MIT",
            "keywords": ["superclaude", "workflow", "agents", "glm", "zcode"],
            "commands": "commands",
            "skills": "skills",
            "agents": "agents",
            "hooks": "hooks/hooks.json",
            "mcpServers": ".mcp.json",
        }
        zdir = out_root / ".zcode-plugin"
        zdir.mkdir(parents=True, exist_ok=True)
        (zdir / "plugin.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

        provenance = {
            "repo": REPO, "ref": args.ref, "commit": sha,
            "rendered_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "plugin_dir": str(out_root),
            "items": [f"{k}:{s}" for k, s, *_ in plan],
        }
        (out_root / "render-manifest.json").write_text(
            json.dumps(provenance, indent=2), encoding="utf-8")

        print(f"\nrendered {len(plan)} component(s) -> {out_root}")
        print("install: ZCode -> Settings -> Plugins -> Create -> Add marketplace,")
        print("         point at this repo (marketplace.json at root covers it),")
        print("         then Install 'superclaude'.")

        if args.install:
            zhome = Path(os.environ.get("ZCODE_HOME", Path.home() / ".zcode"))
            n = 0
            for kind, src, md, siblings, name, target in plan:
                sub = COMPONENTS[kind][1]  # plugin subdir: commands|skills|agents
                dst = zhome / sub / target.relative_to(out_root).relative_to(sub)
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(target, dst)
                n += 1
            print(f"installed {n} file(s) into {zhome} (user scope)")
    finally:
        if tmp:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
