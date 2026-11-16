"""tools/bundle.py opencode: the OpenCode plugin folder with its layers under lib/. It has the plugin, the launcher, the
skill, and the layers; the bundled launcher runs the bridges with lib/ on the path and no path of ours. Run from the
umbrella with the parts beside it; a part that is not there skips the test."""
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARTS = os.path.dirname(HERE)


class OpenCodeBundle(unittest.TestCase):
    def setUp(self):
        for part in ("breadcrumbs-opencode", "breadcrumbs-common", "breadcrumbs-spacegraph"):
            if not os.path.isdir(os.path.join(PARTS, part)):
                self.skipTest("no %s beside this repository" % part)
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.out = os.path.join(tmp.name, "bundle")
        self.done = subprocess.run([sys.executable, os.path.join(HERE, "tools", "bundle.py"), "opencode", self.out],
                                   capture_output=True, text=True, timeout=120)

    def test_the_bundle_builds_and_names_its_commits(self):
        self.assertEqual(self.done.returncode, 0, self.done.stderr[-400:])
        with open(os.path.join(self.out, "BUNDLE.json"), encoding="utf-8") as f:
            info = json.load(f)
        self.assertEqual(info["target"], "opencode")
        self.assertEqual(set(info["sources"]), {"breadcrumbs-opencode", "breadcrumbs-common", "breadcrumbs-spacegraph"})

    def test_the_plugin_folder_has_its_entry_its_launcher_and_its_layers(self):
        self.assertEqual(self.done.returncode, 0, self.done.stderr[-400:])
        for name in ("package.json", os.path.join("plugin", "index.js"), os.path.join("bin", "bc-python"),
                     os.path.join("skills", "dispatch", "SKILL.md"), os.path.join("lib", "breadcrumbs", "core.py"),
                     os.path.join("lib", "breadcrumbs_spacegraph")):
            self.assertTrue(os.path.exists(os.path.join(self.out, name)), name)
        self.assertTrue(os.access(os.path.join(self.out, "bin", "bc-python"), os.X_OK))

    def test_the_bundled_launcher_runs_python_with_the_bundled_layers(self):
        self.assertEqual(self.done.returncode, 0, self.done.stderr[-400:])
        env = {k: v for k, v in os.environ.items() if k not in ("PYTHONPATH", "BREADCRUMBS_HOME")}
        env["XDG_DATA_HOME"] = os.path.join(self.out, "data")
        out = subprocess.run(["sh", os.path.join(self.out, "bin", "bc-python"), "-c",
                              "import breadcrumbs, breadcrumbs_opencode.ace as a, os;"
                              "print(breadcrumbs.__file__);print(os.environ['BREADCRUMBS_HOME'])"],
                             env=env, capture_output=True, text=True, timeout=120)
        self.assertEqual(out.returncode, 0, out.stderr[-400:])
        module, home = out.stdout.splitlines()[-2:]
        self.assertTrue(module.startswith(self.out), module)
        self.assertEqual(home, os.path.join(self.out, "data", "opencode", "breadcrumbs"))


if __name__ == "__main__":
    unittest.main()
