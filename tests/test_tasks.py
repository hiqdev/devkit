"""The template's devkit:* task scripts, as a project runs them: files and leaks in Python, the release ones
in shell. Fake mise, uwiki and gitleaks on PATH record or answer; git is the real one."""

import importlib.util
import os
import shutil
import subprocess
from pathlib import Path

from repo import TASKS, Repo, script

RELEASE = {n: TASKS / f"[% if releases == 'python' %]{n}.sh[% endif %]" for n in ("version", "bump", "release", "up")}


def load(name: str):
    spec = importlib.util.spec_from_file_location(f"devkit_{name}", TASKS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


files, leaks = load("files"), load("leaks")


class Files(Repo):
    def test_git_files_and_ignored_pages_once_each(self):
        self.write(".gitignore", "private/\n.env\n")
        self.write("README.md", "# Home\n")
        self.write("new.txt")
        self.write(".env", "TOKEN=x\n")
        self.write("private/Page.md", "# Page\n")
        self.git("add", ".gitignore", "README.md")
        script(self.bin / "uwiki", 'printf "./README.md\\0./private/Page.md\\0"\n')
        self.assertEqual(files.file_list("."), [".gitignore", "README.md", "new.txt", "private/Page.md"])

    def test_deleted_tracked_files_and_submodules_left_out(self):
        self.write("gone.md")
        self.git("add", "gone.md")
        os.unlink("gone.md")
        script(self.bin / "uwiki", "true\n")
        self.assertEqual(files.file_list("."), [])


class Leaks(Repo):
    def test_config_skips_ignored_paths(self):
        config = leaks.leaks_config([".env", "node_modules/"], None)
        self.assertIn("useDefault = true", config)
        self.assertIn("'''^\\.env$'''", config)
        self.assertIn("'''^node_modules/'''", config)

    def test_config_extends_the_projects_own(self):
        config = leaks.leaks_config([], Path("/p/.gitleaks.toml"))
        self.assertIn("path = '/p/.gitleaks.toml'", config)
        self.assertNotIn("allowlists", config)

    def test_hands_options_to_gitleaks(self):
        script(self.bin / "gitleaks", 'echo "gitleaks $*" > "$(dirname "$0")/gitleaks.log"\n')
        self.assertEqual(leaks.main(["-v"]), 0)
        log = (self.bin / "gitleaks.log").read_text()
        self.assertRegex(log, r"^gitleaks dir --redact --no-banner --config \S+ -v \.$")


class Releases(Repo):
    def setUp(self):
        super().setUp()
        self.write("pkg/__init__.py", '__version__ = "0.1.0"\n')
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "init")
        script(self.bin / "mise", 'echo "$@" >> "$(dirname "$0")/mise.log"\n')
        self.env = dict(os.environ, DEVKIT_VERSION_FILE="pkg/__init__.py", DEVKIT_BRANCH="master")
        # under the names the template renders, as bump and release call version.sh beside them
        self.tasks = self.tmp / "tasks"
        self.tasks.mkdir()
        for name, path in RELEASE.items():
            shutil.copy(path, self.tasks / f"{name}.sh")

    def task(self, name, *args):
        return subprocess.run(
            ["sh", self.tasks / f"{name}.sh", *args], check=False, capture_output=True, text=True, env=self.env
        )

    def tags(self):
        return self.git_out("tag", "--points-at", "HEAD").split()

    def git_out(self, *args):
        return subprocess.run(["git", *args], check=True, capture_output=True, text=True).stdout

    def test_version(self):
        self.assertEqual(self.task("version").stdout, "0.1.0\n")

    def test_bump_tests_commits_and_tags(self):
        r = self.task("bump", "minor")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(Path("pkg/__init__.py").read_text(), '__version__ = "0.2.0"\n')
        self.assertEqual(self.tags(), ["v0.2.0"])
        self.assertEqual((self.bin / "mise.log").read_text(), "run check\n")

    def test_bump_parts(self):
        for part, want in (("patch", "0.1.1"), ("major", "1.0.0")):
            self.assertEqual(self.task("bump", part).returncode, 0)
            self.assertEqual(self.task("version").stdout, want + "\n")

    def test_bump_refuses_a_dirty_tree_and_a_bad_part(self):
        self.assertNotEqual(self.task("bump", "huge").returncode, 0)
        self.write("pkg/other.py")
        r = self.task("bump", "patch")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("commit or stash", r.stderr)
        self.assertEqual(self.tags(), [])

    def test_release_needs_the_tag_on_head(self):
        r = self.task("release")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("not tagged v0.1.0", r.stderr)
        self.assertIn("git tag v0.1.0", r.stderr)  # a version set by hand, no tag yet

    def test_release_refuses_a_tag_on_another_commit(self):
        self.git("tag", "v0.1.0")
        self.write("pkg/other.py")
        self.git("add", "-A")
        self.git("commit", "-qm", "later")
        r = self.task("release")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("tags another commit", r.stderr)

    def test_needs_its_env(self):
        del self.env["DEVKIT_VERSION_FILE"]
        self.assertIn("DEVKIT_VERSION_FILE", self.task("version").stderr)
