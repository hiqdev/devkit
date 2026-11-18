"""devkit: standard tasks for HiQDev projects. Sets them up, updates and checks them.

`devkit init` and `devkit update` copy and merge the template with copier, `devkit doctor` says what is
missing, edited or out of date, and any other command runs the mise task of that name: `devkit lint` is
`mise run lint`. A project needs none of it to lint or release: mise, hk and the template's scripts do.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from . import __version__

SRC = "gh:hiqdev/devkit"
ANSWERS = ".copier-answers.yml"
MISE_CONFIGS = ("mise.toml", ".config/mise/conf.d/devkit.toml")
COMMANDS = ("init", "update", "doctor")
AGENTS = ".config/devkit/AGENTS.md"
MERGED = "keeping the project's own lines"  # the header of a devkit file a project adds its own lines to
SEMVER = re.compile(r"v?(\d+)\.(\d+)\.(\d+)")
UWIKI_MIN = (0, 30, 0)  # uwiki ls --only, which the page steps run


class Fail(Exception):
    """A problem to report in one line, exit 1."""


def run(*cmd: str, capture: bool = False, check: bool = True, **kw) -> subprocess.CompletedProcess:
    try:
        r = subprocess.run(cmd, check=False, text=True, capture_output=capture, **kw)
    except FileNotFoundError:
        raise Fail(f"{cmd[0]} not found: mise install puts the project's tools on PATH") from None
    if check and r.returncode:
        err = (r.stderr or "").strip() if capture else ""
        raise Fail(f"{' '.join(cmd)} exited {r.returncode}" + (f": {err}" if err else ""))
    return r


def out(*cmd: str, **kw) -> str:
    return run(*cmd, capture=True, **kw).stdout


def answers(path: str | Path = ANSWERS) -> dict[str, str]:
    """The answers copier recorded: flat `key: value` lines, as copier writes them."""
    data = {}
    try:
        text = Path(path).read_text()
    except FileNotFoundError:
        return data
    for line in text.splitlines():
        if line.startswith("#") or ":" not in line:
            continue
        key, _, value = line.partition(":")
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
            value = value[1:-1]
        data[key.strip()] = value
    return data


def semver(text: str | None) -> tuple[int, int, int] | None:
    m = SEMVER.match(text or "")
    return (int(m[1]), int(m[2]), int(m[3])) if m else None


# --- init, update: the template ---------------------------------------------------------------


def data_args(pairs: list[str]) -> dict[str, str]:
    data = {}
    for pair in pairs:
        key, sep, value = pair.partition("=")
        if not sep:
            raise Fail(f"-d takes key=value, not {pair}")
        data[key] = value
    return data


def setup(hooks: bool) -> None:
    """Trusts the mise configs, installs the tools, installs the pre-commit hook unless another one rules."""
    for config in MISE_CONFIGS:
        if Path(config).exists():
            run("mise", "trust", "-q", config)
    run("mise", "install")
    if not hooks:
        return
    if hooks_path():
        print(
            f"core.hooksPath is {hooks_path()}: git runs those hooks, not hk's; "
            "git config --unset core.hooksPath, then mise run hooks"
        )
    else:
        run("mise", "run", "hooks")


def hooks_path() -> str:
    return out("git", "config", "--get", "core.hooksPath", check=False).strip()


def migration_hints() -> list[str]:
    """What a project set up before devkit still has, and devkit now does."""
    hints = []
    makefile = Path("Makefile")
    if makefile.exists() and re.search(r"^(lint|check|hooks|links)\s*:", makefile.read_text(), re.MULTILINE):
        hints.append("Makefile has lint targets: move what is the project's own to mise.toml tasks or hk.pkl steps")
    if Path(".githooks").is_dir():
        hints.append(".githooks/: hk installs the pre-commit hook now, remove it")
    for name in (".markdownlint-cli2.yaml", ".markdownlint-cli2.jsonc", ".pre-commit-config.yaml"):
        if Path(name).exists():
            hints.append(f"{name}: devkit's .markdownlint.yaml and hk.pkl take over, move its rules and remove it")
    for p in sorted(Path(".").glob("lychee*.toml")):
        hints.append(f"{p}: devkit's .config/devkit/lychee.toml checks external links now")
    return hints


def cmd_init(args) -> int:
    if Path(ANSWERS).exists():
        raise Fail(f"{ANSWERS} exists, the project is on devkit already: devkit update")
    from copier import run_copy

    run_copy(
        args.src,
        ".",
        data=data_args(args.data),
        vcs_ref=args.ref or f"v{__version__}",
        defaults=args.defaults,
        unsafe=True,
    )
    setup(hooks=not args.no_hooks)
    for hint in migration_hints():
        print(f"- {hint}")
    print("next: mise run lint, then commit what devkit wrote")
    return 0


def conflicted() -> list[str]:
    changed = out("git", "ls-files", "-z", "-mo", "--exclude-standard").split("\0")
    found = []
    for p in sorted({p for p in changed if p}):
        try:
            if re.search(r"^<<<<<<< ", Path(p).read_text(errors="replace"), re.MULTILINE):
                found.append(p)
        except (IsADirectoryError, FileNotFoundError):
            pass
    return found


def local_src(src: str) -> bool:
    """A template on disk, devkit's own checkout for one, rather than a git remote: no tags to compare."""
    return bool(src) and not re.match(r"(gh:|gl:|[a-z+]+://|git@)", src)


def compare_url(src: str, old: str, new: str) -> str | None:
    m = re.match(r"(?:gh:|https://github\.com/)([^/]+/[^/.]+)", src)
    return f"https://github.com/{m[1]}/compare/{old}...{new}" if m and old and new else None


def cmd_update(args) -> int:
    before = answers()
    if not before:
        raise Fail(f"no {ANSWERS}: devkit init sets the project up")
    from copier import run_update

    # a local template, devkit applied to itself, updates to what is committed there, not to its last tag
    to = args.to or ("HEAD" if local_src(before.get("_src_path", "")) else None)
    run_update(
        ".", data=data_args(args.data), vcs_ref=to, defaults=True, overwrite=True, unsafe=True, conflict="inline"
    )
    after = answers()
    pin_uwiki(after)
    setup(hooks=False)
    old, new = before.get("_commit", ""), after.get("_commit", "")
    print(f"devkit {old} -> {new}" if old != new else f"devkit {new}, no change")
    url = compare_url(after.get("_src_path", ""), old, new) if old != new else None
    if url:
        print(f"changes: {url}")
    for p in conflicted():
        print(f"conflict: {p}, resolve the <<<<<<< markers")
    return 0


def uwiki_pinned() -> bool:
    return any(Path(c).exists() and "pipx:hiqsol/uwiki" in Path(c).read_text() for c in MISE_CONFIGS)


def pin_uwiki(a: dict[str, str]) -> None:
    """devkit 0.3.0 left uwiki's version to the project's mise.toml, which `copier update` never writes:
    a project updated from before gets the version it had there."""
    version = a.get("uwiki", "")
    if version and version != "checkout" and not uwiki_pinned():
        run("mise", "use", "-q", "--path", "mise.toml", f"pipx:hiqsol/uwiki@{version}")
        print(f"mise.toml pins uwiki {version} now, the project's to bump: mise use pipx:hiqsol/uwiki@X")


# --- doctor -------------------------------------------------------------------------------------


def latest_tag(src: str) -> str | None:
    m = re.match(r"gh:(.+)", src)
    url = f"https://github.com/{m[1]}" if m else src
    try:
        r = subprocess.run(
            ["git", "ls-remote", "--tags", "--refs", url], check=False, text=True, capture_output=True, timeout=15
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None
    tags = [line.rsplit("/", 1)[-1] for line in r.stdout.splitlines()]
    tags = [t for t in tags if re.fullmatch(r"v\d+\.\d+\.\d+", t)]
    return max(tags, key=semver) if tags else None


def task_names() -> list[str]:
    import json

    r = run("mise", "tasks", "--json", capture=True, check=False)
    try:
        tasks = json.loads(r.stdout or "[]")
    except ValueError:
        return []
    # devkit.toml's own tasks are no clash
    return [t["name"] for t in tasks if not str(t.get("source", "")).endswith("conf.d/devkit.toml")]


def drifted(a: dict[str, str]) -> list[tuple[str, str]]:
    """devkit's files that differ from what the template renders at the project's commit, with its answers:
    edited, or removed, in the project. The project's own files, written once, are left out, and so are
    devkit's that keep the project's own lines (.vale.ini): their header says so.
    Raises Fail when the template does not render: no network, or a commit the template does not have."""
    import warnings

    import yaml
    from copier import run_copy

    src = a.get("_src_path", SRC)
    data = {k: v for k, v in (yaml.safe_load(Path(ANSWERS).read_text()) or {}).items() if not k.startswith("_")}
    with tempfile.TemporaryDirectory(prefix="devkit-doctor-") as tmp:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")  # a local template's uncommitted changes: what doctor takes
                worker = run_copy(
                    src,
                    tmp,
                    data=data,
                    vcs_ref="HEAD" if local_src(src) else a.get("_commit") or None,
                    defaults=True,
                    quiet=True,
                    overwrite=True,
                )
        except Exception as e:  # noqa: BLE001  copier's errors, git's, the network's: a note, not a crash
            raise Fail(f"template {src} not rendered at {a.get('_commit')}: {type(e).__name__}") from None
        own = set(getattr(worker.template, "skip_if_exists", ()) or ())
        found = []
        for f in sorted(Path(tmp).rglob("*")):
            rel = f.relative_to(tmp).as_posix()
            if not f.is_file() or rel == ANSWERS or rel in own:
                continue
            mine = Path(rel)
            if not mine.exists():
                found.append((rel, "missing"))
            elif mine.read_bytes() != f.read_bytes() and MERGED not in f.read_text(errors="replace")[:300]:
                found.append((rel, "edited"))
    return found


def doctor(network: bool = True) -> tuple[list[str], list[str]]:
    """Problems that keep lint or the hook from running as they should, and notes on what is out of date."""
    problems: list[str] = []
    notes: list[str] = []
    a = answers()
    if not a:
        return [f"no {ANSWERS}: not on devkit, devkit init sets it up"], notes

    for config in MISE_CONFIGS:
        if Path(config).exists():
            r = run("mise", "trust", "--show", config, capture=True, check=False)
            if "untrusted" in r.stdout or r.returncode:
                problems.append(f"{config} untrusted: mise trust {config}")
    missing = run("mise", "ls", "--current", "--missing", capture=True, check=False).stdout.split("\n")
    missing = [line.split()[0] for line in missing if line.strip()]
    if missing:
        problems.append(f"tools not installed: {', '.join(missing)}; mise install")

    if a.get("uwiki") != "checkout" and not uwiki_pinned():
        problems.append("mise.toml pins no uwiki: mise use pipx:hiqsol/uwiki@X")
    try:
        got = semver(out("uwiki", "--version", check=False).split()[-1])
    except (Fail, IndexError):
        got = None
    if got and got < UWIKI_MIN:
        problems.append(
            f"uwiki {'.'.join(map(str, got))}: the page steps need {'.'.join(map(str, UWIKI_MIN))} "
            "or later (uwiki ls --only); mise use pipx:hiqsol/uwiki@X"
        )
    if hooks_path():
        problems.append(
            f"core.hooksPath is {hooks_path()}, hk's hook never runs: "
            "git config --unset core.hooksPath, then mise run hooks"
        )
    else:
        hook = Path(out("git", "rev-parse", "--git-path", "hooks/pre-commit").strip())
        if not hook.exists() or "hk" not in hook.read_text(errors="replace"):
            problems.append("no hk pre-commit hook: mise run hooks")

    notes += migration_hints()

    commit = a.get("_commit", "")
    src = a.get("_src_path", SRC)
    if local_src(src):
        commit = ""  # rendered from a checkout, devkit's own: its HEAD, no release to compare with
    if semver(commit) and semver(commit) > semver(__version__):
        notes.append(f"devkit {__version__} is older than the template {commit}: mise up pipx:hiqdev/devkit")
    clash = sorted(set(COMMANDS) & set(task_names()))
    if clash:
        notes.append(f"mise tasks named like devkit commands, devkit runs its own: {', '.join(clash)}; mise run them")
    vale = Path(".vale.ini")
    if vale.exists():
        m = re.search(r"^Packages\s*=\s*(.+)$", vale.read_text(), re.MULTILINE)
        for pkg in m[1].split(",") if m else []:
            if not Path(".vale/styles", pkg.strip()).is_dir():
                notes.append(f"Vale package {pkg.strip()} not synced: lint runs vale sync")
    if Path(AGENTS).exists() and not any(
        Path(f).exists() and AGENTS in Path(f).read_text(errors="replace") for f in ("AGENTS.md", "CLAUDE.md")
    ):
        notes.append(f"neither AGENTS.md nor CLAUDE.md points agents to {AGENTS}: link it from one")
    if network or local_src(src):
        try:
            for path, why in drifted(a):
                notes.append(f"{path} {why}: devkit's, devkit update rewrites it; the project's own goes elsewhere")
        except Fail as e:
            notes.append(f"{e}, edits to devkit's files unchecked")

    if network:
        latest = latest_tag(src) if commit else None
        if latest and semver(commit) and semver(latest) > semver(commit):
            notes.append(f"template {commit}, latest {latest}: devkit update")
        if a.get("uwiki") != "checkout" and shutil.which("mise"):
            current = out("mise", "current", "pipx:hiqsol/uwiki", check=False).strip()
            newest = out("mise", "latest", "pipx:hiqsol/uwiki", check=False).strip()
            if semver(current) and semver(newest) and semver(newest) > semver(current):
                notes.append(f"uwiki {current}, latest {newest}: mise use pipx:hiqsol/uwiki@{newest}")
    return problems, notes


def cmd_doctor(args) -> int:
    problems, notes = doctor(network=not args.offline)
    for p in problems:
        print(f"problem: {p}")
    for n in notes:
        print(f"note: {n}")
    if not problems and not notes:
        print("ok")
    return 1 if problems else 0


# --- the command line ---------------------------------------------------------------------------


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="devkit",
        description="Sets up devkit's lint and release tasks in a project, updates and checks them.",
        epilog="Other commands run the mise task of that name, as mise run does; mise tasks lists them. "
        "Without a command: these commands and the project's tasks.",
    )
    p.add_argument("--version", action="version", version=f"devkit {__version__}")
    sub = p.add_subparsers(dest="command", metavar="COMMAND")

    s = sub.add_parser("init", help="copy devkit into this project, install the tools and the hook")
    s.add_argument("-d", "--data", action="append", default=[], metavar="KEY=VALUE", help="answer a question")
    s.add_argument("--defaults", action="store_true", help="take the defaults of questions not answered by -d")
    s.add_argument("--src", default=SRC, help=f"template, {SRC} by default")
    s.add_argument("--ref", help=f"template tag or commit, v{__version__} by default; HEAD for a local checkout")
    s.add_argument("--no-hooks", action="store_true", help="leave git hooks alone, mise run hooks installs them later")
    s.set_defaults(func=cmd_init)

    s = sub.add_parser("update", help="merge the latest devkit in, keeping the project's own lines")
    s.add_argument("-d", "--data", action="append", default=[], metavar="KEY=VALUE", help="change an answer")
    s.add_argument("--to", metavar="REF", help="tag or commit to update to, the latest tag by default")
    s.set_defaults(func=cmd_update)

    s = sub.add_parser("doctor", help="what keeps lint or the hook from running, what is edited or out of date")
    s.add_argument("--offline", action="store_true", help="skip what needs the network: latest versions, edits")
    s.set_defaults(func=cmd_doctor)

    return p


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        parser().print_help()
        if Path(ANSWERS).exists() and shutil.which("mise"):
            print("\nmise tasks, devkit TASK runs one:")
            sys.stdout.flush()
            subprocess.run(["mise", "tasks"], check=False)
        return 0
    if not argv[0].startswith("-") and argv[0] not in COMMANDS and argv[0] != "help":
        if not shutil.which("mise"):
            print("devkit: mise not found, https://mise.jdx.dev", file=sys.stderr)
            return 1
        os.execvp("mise", ["mise", "run", argv[0], *argv[1:]])
    if argv[0] == "help":
        argv = ["--help"]
    p = parser()
    args = p.parse_args(argv)
    try:
        return args.func(args)
    except Fail as e:
        print(f"devkit: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())
