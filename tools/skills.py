"""Build the dispatch skill and the registered lanes of each plugin from one source.

    python tools/skills.py             write each generated file under the parts folder
    python tools/skills.py --check     write nothing; exit 1 when a file differs from what the source gives
    python tools/skills.py --parts DIR the folder that holds the part folders (default: the folder above this repository)
    python tools/skills.py hermes ...  only these harnesses

Why: one skill teaches the briefs (dispatch) and one hierarchy (a lead and three lanes of models) for each model
family, and each harness has its own command line, tools and limits, and its own way to register a lane. Hand-kept
copies drift. The source is skills/dispatch/: dispatch.md (the text) and lanes.json (the lanes, and the model id and
reasoning level of each lane for each family). Every output is generated, never edited:

    hermes       breadcrumbs_hermes/skills/dispatch/SKILL.md: every family, each with its lane table and the submodel
                 of a profile of that family (delegation.provider, delegation.model, delegation.reasoning_effort)
    codex        skills/dispatch/SKILL.md (the GPT family), profiles/breadcrumbs-<lane>.config.toml for each lane
    claude-code  skills/dispatch/SKILL.md (the Claude family), agents/<lane>.md for each lane

Template syntax, line by line:
    <!-- if hermes codex -->  ...  <!-- end -->     the lines between are kept for these harnesses only (no nesting)
    <!-- if family gpt nvidia --> ... <!-- end -->  the lines between are kept for these model families only
    @@NAME@@                                         a value of the copy (values() below); an unknown name is an error

The files for the public Claude plugin must hold no ACE and no D3M: render() refuses to produce them otherwise.
"""
import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SOURCE = os.path.join(ROOT, "skills", "dispatch")
TEMPLATE = os.path.join(SOURCE, "dispatch.md")
LANES = os.path.join(SOURCE, "lanes.json")

HARNESSES = ("hermes", "codex", "claude-code")
LANE_ORDER = ("lead", "build", "cheap", "check")
# harness -> the family of its copy ("all": every family, one after the other), and the folder of the plugin
FAMILIES = {"hermes": "all", "codex": "gpt", "claude-code": "claude"}
# What Hermes registers the copy with (hermes.py HANDBOOK_ABOUT); the others carry it in their front matter.
HERMES_ABOUT = "Use when you delegate work. Exact crumbs, model lanes."
PART = {"hermes": "breadcrumbs-hermes", "codex": "breadcrumbs-codex", "claude-code": "breadcrumbs-claude"}

TOOLS = {"hermes": "`crumb`, `crumb_find`, the dials in `config.json`, and its command line",
         "codex": "the MCP tools `find`, `open` and `zoom`, the dials in `config.json`, and its command line",
         "claude-code": "the MCP tools `find`, `open` and `zoom`, and its command line"}
OPEN = {"hermes": "`crumb(id, 1)`", "codex": "`open` (the id)", "claude-code": "`open` (the id)"}

# The public Claude plugin has no ACE and no D3M (the ACE adapter and the fold hook live in the private API part).
FORBIDDEN = {
    "claude-code": re.compile(r"\bACE\b|\bace_|\bace\.log|\bfold[ _]hook|\bbc-fold|\bD3M\b|\bclaude-api\b", re.I),
}

MARK = re.compile(r"^<!-- (if|end)(?: (family )?([a-z][a-z -]*))? -->$")
TOKEN = re.compile(r"@@([A-Z0-9_]+)@@")


def read_lanes(path=LANES):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    for fam, spec in data["families"].items():
        if tuple(spec["lanes"]) != LANE_ORDER:
            raise ValueError("family %s: the lanes are not %s" % (fam, ", ".join(LANE_ORDER)))
    return data


def families(lanes, family):
    return list(lanes["families"]) if family == "all" else [family]


def about(lanes, family):
    """The description of the skill (Hermes takes it from register_skill; the others from the front matter)."""
    if family == "all":
        return HERMES_ABOUT
    return "Use when you delegate work. Exact crumbs, %s lanes." % lanes["families"][family]["title"]


def registered_as(harness, lane):
    return {"hermes": {"lead": "the profile's model", "cheap": "the profile's submodel"}.get(lane, "`hermes chat -m`"),
            "codex": "`-p breadcrumbs-%s`" % lane,
            "claude-code": "`breadcrumbs:%s`" % lane}[harness]


def lane_table(lanes, harness, family):
    head = {"hermes": "Hermes", "codex": "Codex profile", "claude-code": "Claude Code agent"}[harness]
    out = []
    for fam in families(lanes, family):
        rows = ["| lane | verbs | model | reasoning | %s |" % head, "|---|---|---|---|---|"]
        for lane in LANE_ORDER:
            cell = lanes["families"][fam]["lanes"][lane]
            model = cell["model"] + "".join(", %s (%s)" % (a["model"], a["provider"]) for a in cell.get("also", ()))
            name = lane + (" (top)" if lanes["lanes"][lane].get("top") else "")
            rows.append("| %s | %s | %s | %s | %s |" % (name, ", ".join(lanes["lanes"][lane]["verbs"]), model,
                                                         cell["effort"], registered_as(harness, lane)))
        if family == "all":
            rows.insert(0, "%s:\n" % lanes["families"][fam]["title"])
        out.append("\n".join(rows))
    return "\n\n".join(out)


def submodels(lanes, family):
    """The commands that give a profile of each family its submodel: the cheap lane of the family."""
    out = []
    for fam in families(lanes, family):
        spec = lanes["families"][fam]
        cell = spec["lanes"]["cheap"]
        out.append("%s profile:\n\n```sh\nhermes config set delegation.provider %s\nhermes config set delegation.model %s\n"
                   "hermes config set delegation.reasoning_effort %s\n```"
                   % (spec["title"], spec["hermes_provider"], cell["model"], cell["effort"]))
    return "\n\n".join(out)


def lockup(lanes, family):
    """The dials example: ace_lockup for the models of the top lanes, each as a glob of its name without a prefix."""
    globs = []
    for fam in families(lanes, family):
        cells = lanes["families"][fam]["lanes"]
        for lane in LANE_ORDER:
            if lanes["lanes"][lane].get("top"):
                glob = "*%s*" % cells[lane]["model"].rsplit("/", 1)[-1]
                if glob not in globs:
                    globs.append(glob)
    return json.dumps({"models": {g: {"ace_lockup": True} for g in globs}})


def values(lanes, harness, family):
    titles = [lanes["families"][f]["title"] for f in families(lanes, family)]
    return {"ABOUT": about(lanes, family), "TOOLS": TOOLS[harness], "OPEN": OPEN[harness],
            "FAMILY": ", ".join(titles[:-1]) + " or " + titles[-1] if len(titles) > 1 else titles[0],
            "LANES": lane_table(lanes, harness, family), "LOCKUP": lockup(lanes, family),
            "SUBMODELS": submodels(lanes, family)}


def refuse_forbidden(text, harness, what):
    bad = FORBIDDEN.get(harness)
    found = bad.search(text) if bad else None
    if found:
        raise ValueError("the %s for %s holds %r, which that plugin must not carry" % (what, harness, found.group(0)))


def render(text, harness, family, lanes=None):
    """The skill for one harness and one family: the blocks of the template kept for both, the values filled in."""
    if harness not in HARNESSES:
        raise KeyError("no such harness: %s" % harness)
    lanes = lanes or read_lanes()
    if family != "all" and family not in lanes["families"]:
        raise KeyError("no such family: %s" % family)
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
            names = (m.group(3) or "").split()
            known = lanes["families"] if m.group(2) else HARNESSES
            unknown = [x for x in names if x not in known]
            if not names or unknown:
                raise ValueError("line %d: none named, or an unknown one: %s" % (n, unknown or "none named"))
            keep = (family == "all" or family in names) if m.group(2) else harness in names
            open_at = n
        else:
            if open_at is None or m.group(2) or m.group(3):
                raise ValueError("line %d: an end with no if, or with names" % n)
            keep, open_at = True, None
    if open_at is not None:
        raise ValueError("the block of line %d is not closed" % open_at)
    vals = values(lanes, harness, family)

    def fill(m):
        if m.group(1) not in vals:
            raise KeyError("no value %s for %s" % (m.group(1), harness))
        return vals[m.group(1)]

    result = TOKEN.sub(fill, "\n".join(out)).lstrip("\n")
    if "@@" in result or "<!--" in result:
        raise ValueError("a token or a marker is left in the copy for %s" % harness)
    refuse_forbidden(result, harness, "copy")
    return result


def claude_agent(lanes, lane):
    """A Claude Code subagent for one lane of the Claude family: name, description, model and effort."""
    spec, cell = lanes["lanes"][lane], lanes["families"]["claude"]["lanes"][lane]
    text = ("---\nname: %s\ndescription: The %s lane (%s). Give it one brief: the user's words with their crumb ids, "
            "the exact pieces, the test for done.\nmodel: %s\neffort: %s\n---\n\n"
            "You are the %s lane of a lead and three lanes. Your verbs: %s. %s\n\n"
            "Do only your verbs. A question that needs a decision goes back to the lead. Your answer is a report: "
            "quote what you rely on with its crumb id or file and line, and say pass or fail for the brief's test.\n"
            % (lane, lane, ", ".join(spec["verbs"]), cell["model"], cell["effort"], lane, ", ".join(spec["verbs"]),
               spec["role"]))
    refuse_forbidden(text, "claude-code", "agent")
    return text


def codex_profile(lanes, lane):
    """A Codex profile for one lane of the GPT family: `codex exec -p breadcrumbs-<lane>`."""
    cell = lanes["families"]["gpt"]["lanes"][lane]
    return ("# Managed by the Breadcrumbs Codex plugin: the %s lane (%s). Generated from lanes.json.\n"
            "model = \"%s\"\nmodel_reasoning_effort = \"%s\"\n"
            % (lane, ", ".join(lanes["lanes"][lane]["verbs"]), cell["model"], cell["effort"]))


def outputs(harness, lanes=None, text=None):
    """{path under the parts folder: contents} of everything generated for one harness."""
    lanes = lanes or read_lanes()
    text = text if text is not None else read_template()
    part, prefix = PART[harness], ("breadcrumbs_hermes/" if harness == "hermes" else "")
    files = {"%s/%sskills/dispatch/SKILL.md" % (part, prefix): render(text, harness, FAMILIES[harness], lanes)}
    for lane in LANE_ORDER:
        if harness == "codex":
            files["%s/profiles/breadcrumbs-%s.config.toml" % (part, lane)] = codex_profile(lanes, lane)
        elif harness == "claude-code":
            files["%s/agents/%s.md" % (part, lane)] = claude_agent(lanes, lane)
    return files


def read_template():
    with open(TEMPLATE, encoding="utf-8") as f:
        return f.read()


def build(parts, harnesses=None, check=False):
    """Write (or, with check, compare) each file. Returns the list of files that differ or are missing."""
    lanes, text, stale = read_lanes(), read_template(), []
    for harness in harnesses or HARNESSES:
        for rel, want in sorted(outputs(harness, lanes, text).items()):
            path = os.path.join(parts, rel)
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
    ap.add_argument("harness", nargs="*", help="only these of: " + ", ".join(HARNESSES))
    ap.add_argument("--parts", default=os.path.dirname(ROOT))
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)
    unknown = [h for h in args.harness if h not in HARNESSES]
    if unknown:
        ap.error("no such harness: %s (one of %s)" % (", ".join(unknown), ", ".join(HARNESSES)))
    stale = build(os.path.abspath(args.parts), args.harness or None, args.check)
    for path in stale:
        print(("differs: " if args.check else "wrote: ") + path)
    if not stale:
        print("all files are what the source gives")
    return 1 if (args.check and stale) else 0


if __name__ == "__main__":
    sys.exit(main())
