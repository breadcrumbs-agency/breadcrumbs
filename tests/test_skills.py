"""tools/skills.py: one template, one copy for each harness, and the public Claude copy keeps clear of ACE and D3M."""
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))

import skills  # noqa: E402


class RenderTest(unittest.TestCase):
    def test_a_block_is_kept_for_the_harnesses_it_names_and_for_no_other(self):
        text = "a\n<!-- if hermes codex -->\nb @@OPEN@@\n<!-- end -->\nc"
        self.assertEqual(skills.render(text, "hermes"), "a\nb `crumb(id, 1)`\nc")
        self.assertEqual(skills.render(text, "codex"), "a\nb `open` (the id)\nc")
        self.assertEqual(skills.render(text, "claude"), "a\nc")

    def test_a_template_with_a_fault_is_refused(self):
        for text in ("<!-- if hermes -->\nx", "x\n<!-- end -->", "<!-- if nobody -->\nx\n<!-- end -->",
                     "<!-- if -->\nx\n<!-- end -->", "<!-- if hermes -->\n<!-- if codex -->\n<!-- end -->\n<!-- end -->",
                     "@@NO_SUCH_VALUE@@"):
            with self.assertRaises((ValueError, KeyError), msg=text):
                skills.render(text, "hermes")

    def test_an_unknown_harness_is_refused(self):
        with self.assertRaises(KeyError):
            skills.render("x", "nobody")

    def test_the_public_claude_copy_refuses_ace_and_d3m(self):
        for word in ("ACE", "ace_lockup", "ace.log", "the fold hook", "D3M", "breadcrumbs-claude-api"):
            with self.assertRaises(ValueError, msg=word):
                skills.render("see " + word, "claude")
        skills.render("see ACE", "hermes")  # the others may name it

    def test_each_harness_gets_a_copy_with_its_own_frontmatter_and_no_marker_left(self):
        text = skills.read_template()
        for harness in skills.TARGETS:
            out = skills.render(text, harness)
            self.assertTrue(out.startswith("---\nname: hierarchy\ndescription: "), harness)
            description = out.split("\n")[2][len("description: "):]
            self.assertEqual(description, skills.VALUES[harness]["ABOUT"])
            self.assertTrue(0 < len(description) <= 60, description)
            self.assertNotIn("<!--", out)
            self.assertNotIn("@@", out)
            self.assertNotIn("\n\n\n", out)

    def test_the_lanes_and_verbs_are_in_every_copy_and_no_copy_holds_a_price_step(self):
        text = skills.read_template()
        for harness in skills.TARGETS:
            out = skills.render(text, harness)
            for word in ("pinpoint", "scaffold", "dispatch", "fan-out", "inspect", "validate", "trim", "orchestrate",
                         "claude-fable-5-2", "gpt-6-astra", "nvidia/nemotron-3-ultra-550b-a55b"):
                self.assertIn(word, out, (harness, word))
            for number in ("100,000", "100000", "94,000", "94000"):
                self.assertNotIn(number, out, (harness, number))

    def test_each_harness_has_its_own_command_line_and_no_other_harnesss(self):
        text = skills.read_template()
        self.assertIn("${HERMES_SKILL_DIR}", skills.render(text, "hermes"))
        self.assertNotIn("${HERMES_SKILL_DIR}", skills.render(text, "codex"))
        self.assertNotIn("${HERMES_SKILL_DIR}", skills.render(text, "claude"))
        self.assertIn("bin/bc-python", skills.render(text, "codex"))
        self.assertNotIn("bin/bc-python", skills.render(text, "claude"))
        self.assertIn("${CLAUDE_PLUGIN_ROOT}/bin/bc", skills.render(text, "claude"))
        self.assertNotIn("CLAUDE_PLUGIN_ROOT", skills.render(text, "hermes"))


class BuildTest(unittest.TestCase):
    def test_build_writes_each_copy_and_check_finds_a_copy_that_was_edited(self):
        with tempfile.TemporaryDirectory() as parts:
            wrote = skills.build(parts)
            self.assertEqual(len(wrote), len(skills.TARGETS))
            self.assertEqual(skills.build(parts, check=True), [])
            path = os.path.join(parts, skills.TARGETS["codex"])
            with open(path, "a", encoding="utf-8") as f:
                f.write("an edit by hand\n")
            self.assertEqual(skills.build(parts, check=True), [path])
            self.assertEqual(skills.build(parts), [path])
            self.assertEqual(skills.build(parts, check=True), [])

    def test_the_copies_in_the_checked_out_parts_are_what_the_template_gives(self):
        parts = os.path.dirname(ROOT)
        if not all(os.path.isfile(os.path.join(parts, t)) for t in skills.TARGETS.values()):
            self.skipTest("the parts are not checked out beside this repository")
        self.assertEqual(skills.build(parts, check=True), [])


if __name__ == "__main__":
    unittest.main()
