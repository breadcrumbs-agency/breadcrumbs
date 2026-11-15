"""tools/skills.py: one source (dispatch.md and lanes.json), one skill for each harness and model family, the lanes
registered the native way of each harness, and the public Claude files keep clear of ACE and D3M."""
import json
import os
import re
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))

import skills  # noqa: E402

VERBS = ("orchestrate", "pinpoint", "scaffold", "dispatch", "fan-out", "inspect", "validate", "trim")


def pairs():
    for harness in skills.HARNESSES:
        yield harness, skills.FAMILIES[harness]


class RenderTest(unittest.TestCase):
    def test_a_block_is_kept_for_the_harnesses_it_names_and_for_no_other(self):
        text = "a\n<!-- if hermes codex -->\nb @@OPEN@@\n<!-- end -->\nc"
        self.assertEqual(skills.render(text, "hermes", "all"), "a\nb `crumb(id, 1)`\nc")
        self.assertEqual(skills.render(text, "codex", "gpt"), "a\nb `open` (the id)\nc")
        self.assertEqual(skills.render(text, "claude-code", "claude"), "a\nc")

    def test_a_family_block_is_kept_for_the_families_it_names_and_for_no_other(self):
        text = "a\n<!-- if family gpt nvidia -->\nb @@FAMILY@@\n<!-- end -->\nc"
        self.assertEqual(skills.render(text, "hermes", "gpt"), "a\nb GPT\nc")
        self.assertEqual(skills.render(text, "hermes", "nvidia"), "a\nb NVIDIA\nc")
        self.assertEqual(skills.render(text, "hermes", "claude"), "a\nc")
        self.assertEqual(skills.render(text, "hermes", "all"), "a\nb Claude, GPT or NVIDIA\nc")

    def test_a_template_with_a_fault_is_refused(self):
        for text in ("<!-- if hermes -->\nx", "x\n<!-- end -->", "<!-- if nobody -->\nx\n<!-- end -->",
                     "<!-- if -->\nx\n<!-- end -->", "<!-- if hermes -->\n<!-- if codex -->\n<!-- end -->\n<!-- end -->",
                     "<!-- if family hermes -->\nx\n<!-- end -->", "<!-- if claude -->\nx\n<!-- end -->",
                     "@@NO_SUCH_VALUE@@"):
            with self.assertRaises((ValueError, KeyError), msg=text):
                skills.render(text, "hermes", "claude")

    def test_an_unknown_harness_or_family_is_refused(self):
        with self.assertRaises(KeyError):
            skills.render("x", "nobody", "claude")
        with self.assertRaises(KeyError):
            skills.render("x", "hermes", "nobody")

    def test_the_public_claude_files_refuse_ace_and_d3m(self):
        for word in ("ACE", "ace_lockup", "ace.log", "the fold hook", "D3M", "breadcrumbs-claude-api"):
            with self.assertRaises(ValueError, msg=word):
                skills.render("see " + word, "claude-code", "claude")
        skills.render("see ACE", "hermes", "claude")  # the others may name it
        for rel, text in skills.outputs("claude-code").items():
            self.assertIsNone(skills.FORBIDDEN["claude-code"].search(text), rel)


class SkillTest(unittest.TestCase):
    def setUp(self):
        self.lanes, self.text = skills.read_lanes(), skills.read_template()

    def test_one_skill_teaches_both_the_briefs_and_the_lanes(self):
        for harness, family in pairs():
            out = skills.render(self.text, harness, family, self.lanes)
            self.assertIn("own words", out, (harness, family))  # the briefs (the old dispatch skill)
            self.assertIn("one lead, three lanes", out, (harness, family))  # the lanes (the old hierarchy skill)
            for verb in VERBS:
                self.assertIn(verb, out, (harness, family, verb))
            self.assertNotIn("<!--", out)
            self.assertNotIn("@@", out)
            self.assertNotIn("\n\n\n", out)

    def test_codex_and_claude_code_carry_front_matter_and_hermes_takes_it_from_register_skill(self):
        for harness, family in pairs():
            out = skills.render(self.text, harness, family, self.lanes)
            if harness == "hermes":
                self.assertTrue(out.startswith("1. Align the least manufactured intent"), family)
                continue
            self.assertTrue(out.startswith("---\nname: dispatch\ndescription: "), harness)
            description = out.split("\n")[2][len("description: "):]
            self.assertEqual(description, skills.about(self.lanes, family))
        for family in list(self.lanes["families"]) + ["all"]:
            self.assertTrue(0 < len(skills.about(self.lanes, family)) <= 60, family)

    def test_each_family_has_its_own_lane_table_and_no_other_familys_ids(self):
        fams = self.lanes["families"]
        for harness, family in pairs():
            if family == "all":  # Hermes: every family, each with its table
                continue
            out = skills.render(self.text, harness, family, self.lanes)
            for lane, cell in fams[family]["lanes"].items():
                self.assertIn(cell["model"], out, (harness, family, lane))
                self.assertIn(skills.registered_as(harness, lane), out, (harness, family, lane))
            for other in fams:
                if other == family:
                    continue
                for cell in fams[other]["lanes"].values():
                    self.assertNotIn(cell["model"], out, (harness, family, other))

    def test_the_dial_example_gears_the_top_lanes_of_the_family(self):
        for harness, family in pairs():
            if harness == "claude-code":
                continue
            out = skills.render(self.text, harness, family, self.lanes)
            cfg = json.loads(re.search(r"```json\n(.*?)\n```", out, re.S).group(1))
            for fam in skills.families(self.lanes, family):
                for lane, cell in self.lanes["families"][fam]["lanes"].items():
                    top = self.lanes["lanes"][lane].get("top", False)
                    matched = any(re.fullmatch(g.replace("*", ".*"), cell["model"]) for g in cfg["models"])
                    self.assertEqual(matched, top, (harness, fam, lane))

    def test_no_copy_holds_a_price_step(self):
        for harness, family in pairs():
            out = skills.render(self.text, harness, family, self.lanes)
            for number in ("100,000", "100000", "94,000", "94000"):
                self.assertNotIn(number, out, (harness, family, number))

    def test_each_harness_has_its_own_command_line_and_no_other_harnesss(self):
        def r(h, f):
            return skills.render(self.text, h, f, self.lanes)
        self.assertIn("${HERMES_SKILL_DIR}", r("hermes", "all"))
        self.assertNotIn("${HERMES_SKILL_DIR}", r("codex", "gpt"))
        self.assertNotIn("${HERMES_SKILL_DIR}", r("claude-code", "claude"))
        self.assertIn("bin/bc-python", r("codex", "gpt"))
        self.assertIn("profiles/breadcrumbs-*.config.toml", r("codex", "gpt"))
        self.assertNotIn("bin/bc-python", r("claude-code", "claude"))
        self.assertIn("${CLAUDE_PLUGIN_ROOT}/bin/bc", r("claude-code", "claude"))
        self.assertNotIn("CLAUDE_PLUGIN_ROOT", r("hermes", "all"))


class RegisteredLanesTest(unittest.TestCase):
    def setUp(self):
        self.lanes = skills.read_lanes()

    def test_claude_code_gets_one_agent_per_lane_with_the_claude_model_and_effort(self):
        files = skills.outputs("claude-code", self.lanes)
        for lane in skills.LANE_ORDER:
            text = files["breadcrumbs-claude/agents/%s.md" % lane]
            head = dict(line.split(": ", 1) for line in text.split("---\n")[1].strip().splitlines())
            cell = self.lanes["families"]["claude"]["lanes"][lane]
            self.assertEqual(head["name"], lane)
            self.assertEqual(head["model"], cell["model"])
            self.assertEqual(head["effort"], cell["effort"])
            self.assertIn(head["effort"], ("low", "medium", "high", "xhigh", "max"))

    def test_codex_gets_one_profile_per_lane_with_the_gpt_model_and_effort(self):
        import tomllib
        files = skills.outputs("codex", self.lanes)
        for lane in skills.LANE_ORDER:
            cfg = tomllib.loads(files["breadcrumbs-codex/profiles/breadcrumbs-%s.config.toml" % lane])
            cell = self.lanes["families"]["gpt"]["lanes"][lane]
            self.assertEqual(cfg, {"model": cell["model"], "model_reasoning_effort": cell["effort"]})

    def test_hermes_gives_each_family_a_submodel_the_cheap_lane_of_that_family(self):
        out = skills.outputs("hermes", self.lanes)["breadcrumbs-hermes/breadcrumbs_hermes/skills/dispatch/SKILL.md"]
        for fam, spec in self.lanes["families"].items():
            cheap = spec["lanes"]["cheap"]
            for line in ("hermes config set delegation.provider %s" % spec["hermes_provider"],
                         "hermes config set delegation.model %s" % cheap["model"],
                         "hermes config set delegation.reasoning_effort %s" % cheap["effort"]):
                self.assertIn(line, out, fam)
            self.assertIn(spec["lanes"]["build"]["model"], out, fam)
        self.assertNotIn("model_map", out)


class BuildTest(unittest.TestCase):
    def test_build_writes_each_file_and_check_finds_a_file_that_was_edited(self):
        with tempfile.TemporaryDirectory() as parts:
            wrote = skills.build(parts)
            self.assertEqual(len(wrote), sum(len(skills.outputs(h)) for h in skills.HARNESSES))
            self.assertEqual(skills.build(parts, check=True), [])
            path = os.path.join(parts, "breadcrumbs-codex", "skills", "dispatch", "SKILL.md")
            with open(path, "a", encoding="utf-8") as f:
                f.write("an edit by hand\n")
            self.assertEqual(skills.build(parts, check=True), [path])
            self.assertEqual(skills.build(parts), [path])
            self.assertEqual(skills.build(parts, check=True), [])

    def test_the_files_in_the_checked_out_parts_are_what_the_source_gives(self):
        parts = os.path.dirname(ROOT)
        if not all(os.path.isdir(os.path.join(parts, p)) for p in skills.PART.values()):
            self.skipTest("the parts are not checked out beside this repository")
        self.assertEqual(skills.build(parts, check=True), [])


if __name__ == "__main__":
    unittest.main()
