"""tools/bundle.py: a bundle is the plugin folder of one part with the layers it reads under lib/. Run from the umbrella
with the parts beside it; a part that is not there skips its test."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARTS = os.path.dirname(HERE)


class CodexBundle(unittest.TestCase):
    def setUp(self):
        for part in ("breadcrumbs-codex", "breadcrumbs-common", "breadcrumbs-spacegraph"):
            if not os.path.isdir(os.path.join(PARTS, part)):
                self.skipTest("no %s beside this repository" % part)
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.out = os.path.join(tmp.name, "bundle")
        done = subprocess.run([sys.executable, os.path.join(HERE, "tools", "bundle.py"), "codex", self.out],
                              capture_output=True, text=True, timeout=120)
        self.assertEqual(done.returncode, 0, done.stderr[-400:])

    def test_the_layers_are_under_lib_and_the_part_holds_no_copy_of_them(self):
        self.assertTrue(os.path.isfile(os.path.join(self.out, "lib", "breadcrumbs", "ace_core.py")))
        self.assertTrue(os.path.isfile(os.path.join(self.out, "lib", "breadcrumbs_spacegraph", "view.py")))
        self.assertFalse(os.path.exists(os.path.join(self.out, "breadcrumbs")))  # the engine is common's, never the part's
        with open(os.path.join(self.out, "BUNDLE.json"), encoding="utf-8") as f:
            self.assertEqual(sorted(json.load(f)["sources"]),
                             ["breadcrumbs-codex", "breadcrumbs-common", "breadcrumbs-spacegraph"])

    def test_the_bundle_runs_with_no_python_path_of_ours(self):
        """Codex starts bin/bc-mcp in the plugin folder: the command line of common must load from lib/ alone."""
        with tempfile.TemporaryDirectory() as home:
            env = {"PATH": os.environ["PATH"], "HOME": home, "CODEX_HOME": home, "PYTHONDONTWRITEBYTECODE": "1"}
            ask = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}) + "\n"
            done = subprocess.run(["sh", "./bin/bc-mcp"], input=ask, capture_output=True, text=True, env=env,
                                  cwd=self.out, timeout=120)
        self.assertEqual(done.returncode, 0, done.stderr[-400:])
        names = {t["name"] for t in json.loads(done.stdout.splitlines()[0])["result"]["tools"]}
        self.assertLessEqual({"find", "open", "zoom"}, names)


class PiBundle(unittest.TestCase):
    def setUp(self):
        for part in ("breadcrumbs-pi", "breadcrumbs-common", "breadcrumbs-spacegraph"):
            if not os.path.isdir(os.path.join(PARTS, part)):
                self.skipTest("no %s beside this repository" % part)
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.out = os.path.join(self.tmp.name, "bundle")
        done = subprocess.run([sys.executable, os.path.join(HERE, "tools", "bundle.py"), "pi", self.out],
                              capture_output=True, text=True, timeout=120)
        self.assertEqual(done.returncode, 0, done.stderr[-400:])

    def test_the_layers_are_under_lib_and_the_part_holds_no_copy_of_them(self):
        self.assertTrue(os.path.isfile(os.path.join(self.out, "lib", "breadcrumbs", "ace_core.py")))
        self.assertTrue(os.path.isfile(os.path.join(self.out, "lib", "breadcrumbs_spacegraph", "view.py")))
        self.assertTrue(os.path.isfile(os.path.join(self.out, "extensions", "breadcrumbs-sync.ts")))
        self.assertFalse(os.path.exists(os.path.join(self.out, "breadcrumbs")))
        with open(os.path.join(self.out, "BUNDLE.json"), encoding="utf-8") as f:
            self.assertEqual(sorted(json.load(f)["sources"]), ["breadcrumbs-common", "breadcrumbs-pi", "breadcrumbs-spacegraph"])

    def test_the_command_of_the_extension_runs_with_the_path_that_it_builds(self):
        """breadcrumbs-sync.ts spawns `python -m breadcrumbs sync pi` with lib/ and the part on PYTHONPATH and nothing else."""
        sessions = os.path.join(self.tmp.name, "sessions")
        os.makedirs(sessions)
        shutil.copy(os.path.join(PARTS, "breadcrumbs-pi", "tests", "fixtures", "real-excerpt.jsonl"), sessions)
        env = {"PATH": os.environ["PATH"], "HOME": self.tmp.name, "PYTHONDONTWRITEBYTECODE": "1", "BREADCRUMBS_SUMMARIZE": "0",
               "PYTHONPATH": os.pathsep.join([os.path.join(self.out, "lib"), self.out]), "PI_CODING_AGENT_SESSION_DIR": sessions,
               "BREADCRUMBS_HOME": os.path.join(self.tmp.name, "memory")}
        done = subprocess.run([sys.executable, "-W", "ignore", "-m", "breadcrumbs", "sync", "pi"], capture_output=True, text=True,
                              env=env, cwd=self.tmp.name, timeout=120)
        self.assertEqual(done.returncode, 0, done.stderr[-400:])
        self.assertEqual(json.loads(done.stdout.splitlines()[-1])["new"], 1)


if __name__ == "__main__":
    unittest.main()
