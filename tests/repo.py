"""A git repo in a temp folder for the tests, fake tools first on PATH."""

import os
import shutil
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASKS = ROOT / "template/.config/mise/tasks/devkit"


def script(path: Path, body: str) -> None:
    path.write_text("#!/bin/sh\n" + body)
    path.chmod(path.stat().st_mode | stat.S_IEXEC)


class Repo(unittest.TestCase):
    """A git repo in a temp folder, the current folder while a test runs, fake tools first on PATH."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.bin = self.tmp / "bin"
        self.bin.mkdir()
        self.dir = self.tmp / "repo"
        self.dir.mkdir()
        self.old = Path.cwd(), os.environ["PATH"]
        os.chdir(self.dir)
        os.environ["PATH"] = f"{self.bin}{os.pathsep}{os.environ['PATH']}"
        self.git("init", "-q")
        self.git("config", "user.email", "test@example.com")
        self.git("config", "user.name", "test")

    def tearDown(self):
        os.chdir(self.old[0])
        os.environ["PATH"] = self.old[1]
        shutil.rmtree(self.tmp, ignore_errors=True)

    def git(self, *args):
        subprocess.run(["git", *args], check=True, capture_output=True)

    def write(self, path, text=""):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(text)
