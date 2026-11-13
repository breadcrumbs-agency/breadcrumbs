"""Build the hierarchy skill of each plugin from one template.

    python tools/skills.py             write each plugin's copy under the parts folder
    python tools/skills.py --check     write nothing; exit 1 when a copy differs from what the template gives
    python tools/skills.py --parts DIR the folder that holds the part folders (default: the folder above this repository)
    python tools/skills.py hermes ...  only these harnesses

Why: the skill teaches one hierarchy (a lead and three lanes of models) to three harnesses, and each harness has its own
command line, tools and limits. Three hand-kept copies drift. The template is skills/hierarchy/hierarchy.md; a copy is
generated, never edited.

Template syntax, line by line:
    <!-- if hermes codex -->  ...  <!-- end -->     the lines between are kept for these harnesses only (no nesting)
    @@NAME@@                                         a value of the harness (VALUES below); an unknown name is an error

The copy for the public Claude plugin must hold no ACE and no D3M: render() refuses to produce it otherwise.
"""
import argparse
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TEMPLATE = os.path.join(ROOT, "skills", "hierarchy", "hierarchy.md")

# harness -> where its copy goes, under the parts folder
TARGETS = {
    "hermes": "breadcrumbs-hermes/breadcrumbs_hermes/skills/hierarchy/SKILL.md",
    "codex": "breadcrumbs-codex/skills/hierarchy/SKILL.md",
    "claude": "breadcrumbs-claude/skills/hierarchy/SKILL.md",
}

ABOUT_DIALS = "Use when you split work across models. Lanes, dials, hive."
VALUES = {
    "hermes": {"ABOUT": ABOUT_DIALS,
               "TOOLS": "`crumb`, `crumb_find`, the dials in `config.json`, and its command line",
               "OPEN": "`crumb(id, 1)`"},
    "codex": {"ABOUT": ABOUT_DIALS,
              "TOOLS": "the MCP tools `find`, `open` and `zoom`, the dials in `config.json`, and its command line",
              "OPEN": "`open` (the id)"},
    "claude": {"ABOUT": "Use when you split work across models. Lanes, caps, hive.",
               "TOOLS": "the MCP tools `find`, `open` and `zoom`, and its command line",
               "OPEN": "`open` (the id)"},
}

# The public Claude plugin has no ACE and no D3M (the ACE adapter and the fold hook live in the private API part).
FORBIDDEN = {
    "claude": re.compile(r"\bACE\b|\bace_|\bace\.log|\bfold[ _]hook|\bbc-fold|\bD3M\b|\bclaude-api\b", re.I),
}

MARK = re.compile(r"^<!-- (if|end)(?: ([a-z ]+))? -->$")
TOKEN = re.compile(r"@@([A-Z0-9_]+)@@")


def render(text, harness):
    """The skill for one harness: the blocks of the template kept for it, its values filled in."""
    if harness not in VALUES:
        raise KeyError("no such harness: %s" % harness)
    out, keep, open_at = [], True, None
    for n, line in enumerate(text.split("\n"), 1):
        m = MARK.match(line)
        if m is None:
            if keep:
                out.append(line)
            continue
        if m.group(1) == "if":
            if open_at is not None:
                raise ValueError("line %d: a block inside the block of line %d" % (n, open_at))
            names = (m.group(2) or "").split()
            unknown = [x for x in names if x not in VALUES]
            if not names or unknown:
                raise ValueError("line %d: no harness, or an unknown one: %s" % (n, unknown or "none named"))
            keep, open_at = harness in names, n
        else:
            if open_at is None:
                raise ValueError("line %d: an end with no if" % n)
            keep, open_at = True, None
    if open_at is not None:
        raise ValueError("the block of line %d is not closed" % open_at)

    def fill(m):
        if m.group(1) not in VALUES[harness]:
            raise KeyError("no value %s for %s" % (m.group(1), harness))
        return VALUES[harness][m.group(1)]

    result = TOKEN.sub(fill, "\n".join(out))
    if "@@" in result or "<!--" in result:
        raise ValueError("a token or a marker is left in the copy for %s" % harness)
    bad = FORBIDDEN.get(harness)
    found = bad.search(result) if bad else None
    if found:
        raise ValueError("the copy for %s holds %r, which that plugin must not carry" % (harness, found.group(0)))
    return result


def read_template():
    with open(TEMPLATE, encoding="utf-8") as f:
        return f.read()


def build(parts, harnesses=None, check=False):
    """Write (or, with check, compare) each copy. Returns the list of copies that differ or are missing."""
    text, stale = read_template(), []
    for harness in harnesses or TARGETS:
        want = render(text, harness)
        path = os.path.join(parts, TARGETS[harness])
        try:
            with open(path, encoding="utf-8") as f:
                have = f.read()
        except OSError:
            have = None
        if have == want:
            continue
        stale.append(path)
        if not check:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(want)
    return stale


def main(argv=None):
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    ap.add_argument("harness", nargs="*", help="only these of: " + ", ".join(sorted(TARGETS)))
    ap.add_argument("--parts", default=os.path.dirname(ROOT))
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)
    unknown = [h for h in args.harness if h not in TARGETS]
    if unknown:
        ap.error("no such harness: %s (one of %s)" % (", ".join(unknown), ", ".join(sorted(TARGETS))))
    stale = build(os.path.abspath(args.parts), args.harness or None, args.check)
    for path in stale:
        print(("differs: " if args.check else "wrote: ") + path)
    if not stale:
        print("all copies are what the template gives")
    return 1 if (args.check and stale) else 0


if __name__ == "__main__":
    sys.exit(main())
