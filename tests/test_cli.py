"""devkit's command line: answers, versions, drift from the template, the mise passthrough.
Fake mise and uwiki on PATH record or answer what devkit asks them; git is the real one."""

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from repo import ROOT, Repo, script

from devkit import cli

SRC = ROOT / "src"


class Pure(unittest.TestCase):
    def test_answers_unquotes_and_skips_comments(self):
        with tempfile.NamedTemporaryFile("w", suffix=".yml", delete=False) as f:
            f.write("# Changes here will be overwritten by Copier\n_commit: v0.3.0\nuwiki: '0.31'\nvault: .\n")
        try:
            self.assertEqual(cli.answers(f.name), {"_commit": "v0.3.0", "uwiki": "0.31", "vault": "."})
        finally:
            os.unlink(f.name)

    def test_answers_missing_file_is_empty(self):
        self.assertEqual(cli.answers("/nonexistent/answers.yml"), {})

    def test_semver_takes_describe_output(self):
        self.assertEqual(cli.semver("v0.2.1-3-gabc"), (0, 2, 1))
        self.assertIsNone(cli.semver("HEAD"))

    def test_compare_url(self):
        self.assertEqual(
            cli.compare_url("gh:hiqdev/devkit", "v0.2.1", "v0.3.0"),
            "https://github.com/hiqdev/devkit/compare/v0.2.1...v0.3.0",
        )
        self.assertIsNone(cli.compare_url("/local/devkit", "v0.2.1", "v0.3.0"))

    def test_local_src(self):
        for src in (".", "/home/me/devkit", "../devkit"):
            self.assertTrue(cli.local_src(src), src)
        for src in ("gh:hiqdev/devkit", "https://github.com/hiqdev/devkit.git", "git@github.com:hiqdev/devkit", ""):
            self.assertFalse(cli.local_src(src), src)


class Passthrough(Repo):
    def run_devkit(self, *args):
        env = dict(os.environ, PYTHONPATH=str(SRC))
        return subprocess.run(
            [sys.executable, "-m", "devkit", *args], check=False, capture_output=True, text=True, env=env
        )

    def test_other_commands_run_the_mise_task(self):
        script(self.bin / "mise", 'echo "mise $*"\n')
        self.assertEqual(self.run_devkit("lint", "--x").stdout, "mise run lint --x\n")
        # the release commands are mise tasks now, devkit:bump and the others run them
        self.assertEqual(self.run_devkit("patch").stdout, "mise run patch\n")

    def test_other_commands_refuse_unknown_options(self):
        r = self.run_devkit("doctor", "--nope")
        self.assertEqual(r.returncode, 2)
        self.assertIn("--nope", r.stderr)

    def test_init_refuses_a_project_on_devkit(self):
        self.write(".copier-answers.yml", "_commit: v0.3.0\n")
        r = self.run_devkit("init")
        self.assertEqual(r.returncode, 1)
        self.assertIn("devkit update", r.stderr)

    def test_migration_hints(self):
        self.write("Makefile", "lint:\n\ttrue\n")
        self.write(".githooks/pre-commit")
        self.write("lychee-external.toml")
        hints = "\n".join(cli.migration_hints())
        self.assertIn("Makefile", hints)
        self.assertIn(".githooks", hints)
        self.assertIn("lychee-external.toml", hints)

    def test_ruff_unextended(self):
        self.write(cli.RUFF, "line-length = 120\n")
        self.assertIsNone(cli.ruff_unextended({"python": "false"}))
        self.assertIn("extend", cli.ruff_unextended({"python": "true"}))
        self.write("pyproject.toml", "[tool.ruff]\nline-length = 100\n")
        self.assertIn("extend", cli.ruff_unextended({"python": "true"}))
        self.write("pyproject.toml", f'[tool.ruff]\nextend = "{cli.RUFF}"\n')
        self.assertIsNone(cli.ruff_unextended({"python": "true"}))


class Drift(Repo):
    """A project rendered from this checkout's template: doctor finds devkit's files edited or removed."""

    def setUp(self):
        super().setUp()
        cmd = ["copier", "copy", "-q", "--trust", "--defaults", "--vcs-ref", "HEAD", str(ROOT), "."]
        subprocess.run(cmd, check=True, capture_output=True)

    def test_unchanged_is_no_drift(self):
        self.assertEqual(cli.drifted(cli.answers()), [])

    def test_edited_and_missing_but_not_the_projects_own(self):
        self.write(".config/devkit/lychee.toml", "edited\n")
        os.unlink(".config/devkit/hk-steps.pkl")
        for own in ("mise.toml", "hk.pkl", ".vale.ini", "AGENTS.md"):  # .vale.ini keeps the project's own lines
            Path(own).write_text(Path(own).read_text() + "# own\n")
        self.assertEqual(
            cli.drifted(cli.answers()),
            [(".config/devkit/hk-steps.pkl", "missing"), (".config/devkit/lychee.toml", "edited")],
        )


if __name__ == "__main__":
    unittest.main()
