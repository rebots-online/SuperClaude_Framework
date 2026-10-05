#!/usr/bin/env python3
"""
import_superclaude.py - import SuperClaude framework components as Devin skills.

Fetches SuperClaude-Org/SuperClaude_Framework (the plugins/superclaude tree),
translates Claude Code conventions into Devin SKILL.md format, and installs
into Devin's skills directory. The full plugin tree is vendored alongside the
skills dir so imported bodies can resolve supporting files.

Stdlib only. Windows/macOS/Linux.

Examples:
  python import_superclaude.py --list
  python import_superclaude.py                      # skills only, global scope
  python import_superclaude.py --components all
  python import_superclaude.py --components skills,commands --scope project
  python import_superclaude.py --ref v4.1.0 --force
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

# component -> source subdir inside the plugin tree
COMPONENT_DIRS = {
    "skills": "skills",      # <name>/SKILL.md + sibling files
    "commands": "commands",  # <name>.md   (the /sc:* commands)
    "agents": "agents",      # <name>.md   (persona subagents)
    "modes": "modes",        # MODE_<Name>.md
}

# Claude Code tool names -> Devin tool names (allowed-tools translation).
# mcp__* entries pass through verbatim; unknown names are dropped with a note.
TOOL_MAP = {
    "read": "read",
    "write": "write",
    "edit": "edit",
    "multiedit": "edit",
    "grep": "grep",
    "glob": "glob",
    "ls": "glob",
    "bash": "exec",
    "webfetch": "webfetch",
    "websearch": "web_search",
    "todowrite": "todo_write",
    "task": "run_subagent",
    "notebookedit": "notebook_edit",
    "slashcommand": "skill",
}

# frontmatter fields Devin understands; everything else is dropped into a
# provenance comment in the body rather than emitted verbatim.
DEVIN_FIELDS = {
    "name", "description", "argument-hint", "model", "subagent", "agent",
    "allowed-tools", "permissions", "triggers",
}
DROP_MODELS = {"inherit", "haiku"}


class RawBlock(str):
    """Frontmatter value captured verbatim (nested maps like permissions:)."""


# ---------------------------------------------------------------- frontmatter

def _scalar(v):
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        v = v[1:-1]
    if v.lower() in ("true", "false"):
        return v.lower() == "true"
    return v


def parse_frontmatter(text):
    """Parse the simple YAML subset SKILL.md files use. Returns (dict, body)."""
    text = text.replace("\r\n", "\n")
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", text, re.S)
    if not m:
        return {}, text
    raw, body = m.group(1), m.group(2)
    fm, key, block = {}, None, []
    for line in raw.split("\n"):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(line) - len(line.lstrip())
        mm = re.match(r"^([A-Za-z0-9_-]+)\s*:\s*(.*)$", line.lstrip())
        if mm and indent == 0:
            key = mm.group(1)
            val = mm.group(2).strip()
            block = []
            if val == "":
                fm[key] = block  # may become list or RawBlock below
            elif val.startswith("[") and val.endswith("]"):
                fm[key] = [_scalar(x) for x in val[1:-1].split(",") if x.strip()]
            else:
                fm[key] = _scalar(val)
        elif indent > 0 and key is not None and isinstance(fm.get(key), list):
            if stripped.startswith("- "):
                fm[key].append(_scalar(stripped[2:]))
            else:
                # nested map line (e.g. under permissions:) -> keep raw
                if not isinstance(fm[key], RawBlock):
                    fm[key] = RawBlock(key)
                fm[key] = RawBlock((fm[key] + "\n" + line).lstrip("\n"))
    for k, v in list(fm.items()):
        if isinstance(v, list) and not v:
            fm[k] = None
        elif isinstance(v, RawBlock):
            pass
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
            out.append(f"{k}:")
            out += [f"  - {_emit_scalar(i)}" for i in v]
        elif isinstance(v, bool):
            out.append(f"{k}: {'true' if v else 'false'}")
        else:
            out.append(f"{k}: {_emit_scalar(v)}")
    out.append("---")
    return "\n".join(out)


# ------------------------------------------------------------- translation

def translate_tools(tools):
    out, dropped = [], []
    for t in tools or []:
        t = str(t).strip()
        if not t:
            continue
        if t.startswith("mcp__"):
            out.append(t)
            continue
        mapped = TOOL_MAP.get(t.lower().replace(" ", ""))
        if mapped:
            if mapped not in out:
                out.append(mapped)
        else:
            dropped.append(t)
    return out, dropped


def slugify(name):
    s = re.sub(r"[^a-zA-Z0-9]+", "-", name).strip("-").lower()
    return s or "unnamed"


def skill_name(kind, src_name, prefix):
    """Final installed skill directory name for a source component."""
    if kind == "skills":
        base = slugify(src_name)
    elif kind == "commands":
        base = slugify(src_name)
    elif kind == "agents":
        base = f"agent-{slugify(src_name)}"
    elif kind == "modes":
        base = f"mode-{slugify(src_name)}"
    if kind == "commands" and base == "sc":
        return "sc"  # the /sc namespace index stays '/sc'
    return f"{prefix}{base}"


def convert_file(text, *, kind, dname, src_rel, vendor_posix, sha, prefix):
    """Translate one source .md into Devin SKILL.md content."""
    fm, body = parse_frontmatter(text)
    notes = []

    # namespace/type rewrites that differ per component kind
    if kind == "agents":
        fm["subagent"] = True

    # Claude-only field translations
    if fm.get("context") == "fork":
        fm.pop("context")
        fm.setdefault("subagent", True)
        notes.append("context: fork -> subagent: true")
    if fm.get("disable-model-invocation") is True:
        fm.pop("disable-model-invocation")
        fm["triggers"] = ["user"]
        notes.append("disable-model-invocation -> triggers: [user]")
    if fm.get("user-invocable") is False:
        fm.pop("user-invocable")
        fm["triggers"] = ["model"]
        notes.append("user-invocable: false -> triggers: [model]")

    # allowed-tools may be a comma string, list, or absent
    tools = fm.get("allowed-tools") or fm.get("allowed_tools")
    if isinstance(tools, str):
        tools = [t.strip() for t in tools.split(",")]
    if isinstance(tools, list):
        mapped, dropped = translate_tools(tools)
        fm.pop("allowed-tools", None)
        fm.pop("allowed_tools", None)
        if mapped:
            fm["allowed-tools"] = mapped
        if dropped:
            notes.append(f"dropped tools (no Devin equivalent): {', '.join(dropped)}")

    model = fm.get("model")
    if isinstance(model, str) and model.strip().lower() in DROP_MODELS:
        fm.pop("model")
        notes.append(f"dropped model: {model}")

    fm["name"] = dname
    if "description" not in fm or not fm["description"]:
        fm["description"] = f"SuperClaude {kind[:-1]}: {dname}"

    # fold unknown frontmatter fields into a provenance note
    extra = {k: v for k, v in fm.items() if k not in DEVIN_FIELDS and v is not None}
    fm = {k: v for k, v in fm.items() if k in DEVIN_FIELDS}
    if extra:
        rendered = ", ".join(
            f"{k}={v if not isinstance(v, RawBlock) else '<block>'}" for k, v in extra.items()
        )
        notes.append(f"unmapped fields: {rendered}")

    # body adaptation: namespace + path rewrites
    body = body.replace("/sc:", "/sc-")
    body = body.replace("${CLAUDE_PLUGIN_ROOT}", vendor_posix)
    body = body.replace("~/.claude/", vendor_posix + "/")

    header = (
        f"<!-- Imported from SuperClaude Framework ({REPO}@{sha})\n"
        f"     Source: {src_rel}\n"
        f"     Vendored plugin tree: {vendor_posix}\n"
    )
    if notes:
        header += "     Translation notes: " + "; ".join(notes) + "\n"
    header += "-->\n\n"

    ordered = {}
    for k in ("name", "description", "argument-hint", "model", "subagent",
              "agent", "allowed-tools", "permissions", "triggers"):
        if k in fm:
            ordered[k] = fm[k]
    return dump_frontmatter(ordered) + "\n\n" + header + body


# ------------------------------------------------------------------- source

def resolve_dirs(scope, cwd):
    if scope == "project":
        base = Path(cwd) / ".devin"
    else:
        if sys.platform == "win32":
            base = Path(os.environ.get("APPDATA", Path.home() / "AppData/Roaming")) / "devin"
        else:
            base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "devin"
    return base / "skills", base / "superclaude"


def fetch_source(ref, repo_dir):
    """Return (repo_path, sha, tmpdir_or_None)."""
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

    tmp = Path(tempfile.mkdtemp(prefix="superclaude-"))
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


# ------------------------------------------------------------------ install

def iter_components(plugin, components):
    """Yield (kind, src_name, md_path, siblings) for each importable item."""
    for kind in components:
        cdir = plugin / COMPONENT_DIRS[kind]
        if not cdir.is_dir():
            print(f"warning: {cdir} missing, skipping {kind}", file=sys.stderr)
            continue
        if kind == "skills":
            for d in sorted(cdir.iterdir()):
                md = d / "SKILL.md"
                if d.is_dir() and md.is_file():
                    siblings = [f for f in d.iterdir() if f.name != "SKILL.md" and f.is_file()]
                    yield kind, d.name, md, siblings
        else:
            for f in sorted(cdir.glob("*.md")):
                stem = f.stem
                if kind == "modes":
                    stem = re.sub(r"^MODE_?", "", stem)
                yield kind, stem, f, []


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--components", default="skills",
                    help="comma list: skills,commands,agents,modes or 'all' (default: skills)")
    ap.add_argument("--scope", choices=["global", "project"], default="global",
                    help="global -> Devin user skills dir; project -> <cwd>/.devin/skills")
    ap.add_argument("--prefix", default=None,
                    help="installed-name prefix (default 'sc-'; pass '' to disable)")
    ap.add_argument("--ref", default=DEFAULT_REF, help="git ref to import (default master)")
    ap.add_argument("--repo-dir", help="use an existing local clone instead of fetching")
    ap.add_argument("--skills-dir", help="override skills install dir")
    ap.add_argument("--vendor-dir", help="override vendor dir (default: sibling 'superclaude' of skills dir)")
    ap.add_argument("--vendor-link",
                    help="don't copy the plugin tree; reference this existing path in generated files")
    ap.add_argument("--list", action="store_true", help="list importable items, write nothing")
    ap.add_argument("--dry-run", action="store_true", help="show planned writes, write nothing")
    ap.add_argument("--force", action="store_true",
                    help="overwrite skill dirs not recorded in the import manifest")
    args = ap.parse_args()

    prefix = "sc-" if args.prefix is None else args.prefix
    components = list(COMPONENT_DIRS) if args.components == "all" else [
        c.strip() for c in args.components.split(",") if c.strip()]
    bad = [c for c in components if c not in COMPONENT_DIRS]
    if bad:
        sys.exit(f"unknown components: {bad} (choose from {list(COMPONENT_DIRS)} or 'all')")

    skills_dir, vendor_dir = resolve_dirs(args.scope, Path.cwd())
    if args.skills_dir:
        skills_dir = Path(args.skills_dir)
    if args.vendor_dir:
        vendor_dir = Path(args.vendor_dir)
    repo_path, sha, tmp = fetch_source(args.ref, args.repo_dir)
    try:
        plugin = repo_path / PLUGIN_SUBDIR
        if not plugin.is_dir():
            sys.exit(f"plugin tree not found at {PLUGIN_SUBDIR} in {repo_path}")

        items = list(iter_components(plugin, components))
        if args.list:
            for kind, src, md, sib in items:
                print(f"{kind:8} {src:28} -> /{skill_name(kind, src, prefix)}")
            print(f"\n{len(items)} item(s) from {REPO}@{sha}")
            return

        manifest_path = (skills_dir.parent / "import-manifest.json"
                         if args.vendor_link else vendor_dir / "import-manifest.json")
        prev = set()
        if manifest_path.is_file():
            try:
                prev = set(json.loads(manifest_path.read_text()).get("installed", []))
            except Exception:
                pass

        if args.vendor_link:
            vend = None
            vendor_posix = Path(args.vendor_link).as_posix()
        else:
            vend = vendor_dir / "plugin"
            vendor_posix = vend.as_posix()
        # Devin has one skill namespace; upstream has parallel skills/ and
        # commands/ dirs that can collide (brainstorm, pm, troubleshoot).
        # Priority: skills > commands. Losers get a -cmd style suffix.
        kind_rank = {"skills": 0, "agents": 1, "modes": 2, "commands": 3}
        plan, taken = [], {}
        for kind, src, md, siblings in items:
            dname = skill_name(kind, src, prefix)
            if dname in taken:
                other_kind = taken[dname]
                if kind_rank[kind] > kind_rank[other_kind]:
                    dname = f"{dname}-{kind[:-1]}"
                else:
                    # current item outranks the earlier one; suffix the earlier
                    for i, p in enumerate(plan):
                        if p[4] == dname:
                            nd = f"{dname}-{p[0][:-1]}"
                            nt = skills_dir / nd
                            plan[i] = (p[0], p[1], p[2], p[3], nd, nt,
                                       nt.exists() and nd not in prev)
                            taken[nd] = p[0]
                            break
            taken[dname] = kind
            target = skills_dir / dname
            foreign = target.exists() and dname not in prev
            plan.append((kind, src, md, siblings, dname, target, foreign))

        for kind, src, md, siblings, dname, target, foreign in plan:
            tag = "SKIP(foreign)" if foreign and not args.force else "write"
            print(f"  {tag:14} {kind:8} {src:24} -> {target}")
        if args.dry_run:
            print(f"\ndry-run: {len(plan)} item(s), target {skills_dir}")
            return

        skills_dir.mkdir(parents=True, exist_ok=True)
        # vendor the whole plugin tree so imported bodies can resolve references
        if vend is not None:
            vend.mkdir(parents=True, exist_ok=True)
            shutil.copytree(plugin, vend, dirs_exist_ok=True)

        installed, skipped = [], []
        for kind, src, md, siblings, dname, target, foreign in plan:
            if foreign and not args.force:
                skipped.append(dname)
                continue
            target.mkdir(parents=True, exist_ok=True)
            src_rel = md.relative_to(repo_path).as_posix()
            content = convert_file(
                md.read_text(encoding="utf-8"), kind=kind, dname=dname,
                src_rel=src_rel, vendor_posix=vendor_posix, sha=sha, prefix=prefix)
            (target / "SKILL.md").write_text(content, encoding="utf-8")
            for s in siblings:
                shutil.copy2(s, target / s.name)
            installed.append(dname)

        manifest = {
            "repo": REPO, "ref": args.ref, "commit": sha,
            "imported_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "scope": "custom" if args.skills_dir else args.scope,
            "components": components,
            "skills_dir": str(skills_dir),
            "vendor_dir": vendor_posix if args.vendor_link else str(vendor_dir),
            "installed": sorted(set(prev) | set(installed)),
        }
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

        print(f"\ninstalled {len(installed)} skill(s) -> {skills_dir}")
        if vend is not None:
            print(f"vendored plugin tree    -> {vend}")
        else:
            print(f"referenced plugin tree  -> {vendor_posix}")
        if skipped:
            print(f"skipped {len(skipped)} pre-existing dir(s) not from prior import "
                  f"(use --force to overwrite): {', '.join(skipped)}")
        print("restart the session (or run /skills) for new entries to appear in '/' completions")
    finally:
        if tmp:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
