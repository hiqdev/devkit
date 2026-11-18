# Setup

## Install

[mise](https://mise.jdx.dev) first, then the command, once per machine:

```sh
mise use -g pipx:hiqdev/devkit
```

It sets projects up and updates them. A project needs no devkit to lint, hook or release: its tasks run mise,
hk and the scripts devkit wrote into it, so a clone needs `mise install` only, and so does CI.

## A new project

```sh
git init && devkit init       # asks the questions below, copies the files, mise trust, mise install, the hook
mise run check                # every check, green on a fresh project: no tests yet, a warning says so
git add -A && git commit -m 'devkit'
```

`devkit init -d ci=gitlab -d wrap=true --defaults` answers on the command line and takes the defaults for the
rest. `--no-hooks` leaves git hooks alone: see [Troubleshooting](Troubleshooting.md#worktrees-share-the-hook)
for why a worktree wants that.

## A project with its own lint

Run `devkit init` on a clean tree, so `git diff` shows what it wrote. It writes devkit's files and the
project's ones that are missing, never one that exists: `mise.toml` and `hk.pkl` stay as they were.
Then it lists what the project has that devkit does now:

- **Makefile lint targets:** a check of the project's own becomes an `hk.pkl` step, any other target a
  `mise.toml` task under the same name, and the Makefile goes, so there is one runner.
- **`.githooks/` or `core.hooksPath`:** git runs those hooks, not hk's: `git config --unset core.hooksPath`,
  then `mise run hooks`.
- **`.markdownlint-cli2.yaml` or `.jsonc`:** its rules move to `.markdownlint.yaml`, which extends devkit's.
- **`.pre-commit-config.yaml`:** its checks become `hk.pkl` steps, or are devkit's already.
- **`lychee*.toml`:** devkit's `.config/devkit/lychee.toml` takes over.

`mise.toml` needs a uwiki pin if it had none: `mise use pipx:hiqsol/uwiki@X`. Then:

1. `mise run check` and fix what it finds. A finding in many files at once is usually one rule that does not fit:
   change it in the project's file, see [A project's own](Customizing.md).
2. CI: the GitHub workflow needs nothing more, a GitLab project names devkit's jobs, see [CI](CI.md).
3. `devkit doctor` until it reports no problem.

A pre-existing problem lint finds goes into a commit of its own, before the devkit one, so that one stays
readable.

## Questions

copier records the answers in `.copier-answers.yml`; `devkit update -d KEY=VALUE` changes one later.

| question | default | |
|---|---|---|
| `vault` | `.` | folder uwiki checks as the vault, from the project root |
| `uwiki` | `0.31.0` | uwiki release `mise.toml` pins at first; `checkout` in uwiki's own repo runs its `.venv` |
| `ci` | `github` | `github` writes a workflow, `gitlab` hidden jobs `.gitlab-ci.yml` extends, or `none` |
| `wrap` | `false` | lint checks paragraphs and list items are wrapped: `uwiki wrap --check` |
| `python` | `false` | lint runs `ruff check` and `ruff format --check`, rules in `.config/devkit/ruff.toml`, which `pyproject.toml` extends |
| `releases` | `none` | `python`: the release commands, see [Releases](Releases.md) |
| `version_file` | `src/NAME/__init__.py` | with `releases = python`: holds `__version__ = "X.Y.Z"` |
| `package` | `pipx:hiqsol/NAME` | with `releases = python`: the mise package `mise run up` installs |
| `command` | `NAME` | with `releases = python`: the command whose `--version` `mise run up` checks |
| `branch` | `master` | with `releases = python`: the branch `mise run release` pushes with the tag |

`NAME` is the project folder's name.

## Without the command

The command runs these, for a machine without it:

```sh
uvx copier copy --trust gh:hiqdev/devkit .
mise trust mise.toml && mise trust .config/mise/conf.d/devkit.toml && mise install
mise run hooks
mise run check
```
