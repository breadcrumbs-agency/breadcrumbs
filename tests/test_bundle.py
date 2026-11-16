"""tools/bundle.py: a bundle is the plugin folder of one part with the layers it reads under lib/. Run from the umbrella
with the parts beside it; a part that is not there skips its test."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import tomllib
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARTS = os.path.dirname(HERE)


class HermesBundle(unittest.TestCase):
    def test_the_pages_and_films_of_the_part_are_not_in_the_bundle(self):
        """doc/ and docs/ are the project's pages: not plugin code, and one film's data (622 KB of hashes) makes Hermes's
        install scan answer "dangerous", which --force does not override."""
        for part in ("breadcrumbs-hermes", "breadcrumbs-common", "breadcrumbs-spacegraph"):
            if not os.path.isdir(os.path.join(PARTS, part)):
                self.skipTest("no %s beside this repository" % part)
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "bundle")
            done = subprocess.run([sys.executable, os.path.join(HERE, "tools", "bundle.py"), "hermes", out],
                                  capture_output=True, text=True, timeout=120)
            self.assertEqual(done.returncode, 0, done.stderr[-400:])
            self.assertTrue(os.path.isfile(os.path.join(out, "plugin.yaml")))
            for pages in ("doc", "docs"):
                self.assertFalse(os.path.exists(os.path.join(out, pages)), pages)
            self.assertTrue(os.path.isfile(os.path.join(out, "lib", "breadcrumbs_spacegraph", "qr.py")))

    def test_the_harness_icon_is_in_the_bundle_and_declared_as_package_data(self):
        """The harness adapter reads its icon beside the package, including from a generated release bundle."""
        for part in ("breadcrumbs-hermes", "breadcrumbs-common", "breadcrumbs-spacegraph"):
            if not os.path.isdir(os.path.join(PARTS, part)):
                self.skipTest("no %s beside this repository" % part)
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "bundle")
            done = subprocess.run([sys.executable, os.path.join(HERE, "tools", "bundle.py"), "hermes", out],
                                  capture_output=True, text=True, timeout=120)
            self.assertEqual(done.returncode, 0, done.stderr[-400:])
            icon = os.path.join(out, "breadcrumbs_hermes", "icon.png")
            self.assertTrue(os.path.isfile(icon))
            with open(os.path.join(out, "pyproject.toml"), "rb") as f:
                package_data = tomllib.load(f)["tool"]["setuptools"]["package-data"]["breadcrumbs_hermes"]
            self.assertIn("icon.png", package_data)


class ClaudeApiBundle(unittest.TestCase):
    """The private API side builds as the Claude plugin folder with lib/, and --publish refuses (no release repository)."""

    def setUp(self):
        for part in ("breadcrumbs-claude-api", "breadcrumbs-common", "breadcrumbs-spacegraph"):
            if not os.path.isdir(os.path.join(PARTS, part)):
                self.skipTest("no %s beside this repository" % part)
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.out = os.path.join(tmp.name, "bundle")
        self.done = subprocess.run([sys.executable, os.path.join(HERE, "tools", "bundle.py"), "claude-api", self.out],
                                   capture_output=True, text=True, timeout=120)

    def test_the_bundle_has_the_plugin_the_layers_and_the_proxy(self):
        self.assertEqual(self.done.returncode, 0, self.done.stderr[-400:])
        for rel in (".claude-plugin/plugin.json", "bin/bc-proxy", "bin/bc-fold", "breadcrumbs_proxy/proxy.py",
                    "breadcrumbs_claude/ace_adapter.py", "lib/breadcrumbs/ace_core.py", "BUNDLE.json"):
            self.assertTrue(os.path.isfile(os.path.join(self.out, rel)), rel)
        with open(os.path.join(self.out, "BUNDLE.json"), encoding="utf-8") as f:
            self.assertEqual(json.load(f)["target"], "claude-api")

    def test_publish_refuses_until_a_release_repository_is_configured(self):
        self.assertEqual(self.done.returncode, 0, self.done.stderr[-400:])
        done = subprocess.run([sys.executable, os.path.join(HERE, "tools", "bundle.py"), "claude-api",
                               self.out + "-pub", "--publish"], capture_output=True, text=True, timeout=120)
        self.assertNotEqual(done.returncode, 0)
        self.assertIn("no release repository configured", done.stderr)


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
