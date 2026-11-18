# Development

## Layout

- `copier.yml`: the questions and copier's settings
- `template/`: the files copier renders into a project, `.jinja` ones through Jinja
- `src/devkit/`: the command, `cli.py`; Python 3.11 or later, copier its only dependency
- `template/.config/mise/tasks/devkit/`: the scripts behind the tasks, the same in every project
- `tests/test_cli.py`: the command's unit tests, `tests/test_tasks.py` the scripts'
- `test.sh`: renders the template as projects and lints each
- `docs/`: these pages, a uwiki vault with `README.md`
- the rest is devkit applied to itself, see [devkit on itself](#devkit-on-itself)

## devkit on itself

devkit is a project of its own template, with `releases = python` and `python = true`: its lint checks the
docs, the command, `test.sh`, and its releases are `mise run patch` and `mise run release`. The template lives in
`template/`, so devkit's copies of its files sit at the root next to it, as in any project:
`.config/devkit/`, `.config/mise/conf.d/devkit.toml`, `.github/workflows/lint.yml` and `release.yml`,
`.vale.ini`; and the ones written once, `mise.toml` and `hk.pkl`.

One thing differs: `.copier-answers.yml` has `_src_path: .`, the template is this checkout: `devkit update`
takes its HEAD, `devkit doctor` compares no tags and checks devkit's copies against the checkout. devkit's
own `mise.toml` has a `venv` task (`uv sync`) for the command and copier, which `unit` and `self` depend on;
lint needs neither.

A change to the template reaches devkit's own copies with `mise run self`, which renders this checkout's
template over them, the files written once left alone. `test.sh` fails while one differs from what the
template renders, so a change of the template and of devkit's copies land together.

devkit's tasks, `mise.toml`:

| task | does |
|---|---|
| `mise run unit` | the command's unit tests |
| `mise run test` | `unit`, then `test.sh` |
| `mise run self` | the template over devkit's own copies of its files |
| `mise run lint`, `fix`, `hooks` | as in any project |
| `mise run minor`, `mise run release` | a devkit release, see [releasing devkit](#releasing-devkit) |

## Template conventions

- hk and mise use `{{ }}` themselves, so the template's Jinja is `[[ ]]`, `[% %]` and `[# #]`.
- A file devkit owns starts with `Managed by devkit (github.com/hiqdev/devkit)` and how it changes:
  `devkit update` rewrites or merges it.
- A file the project owns is listed in `copier.yml` `_skip_if_exists`: written once, never again.
- A file only some projects get has its condition in its name:
  `[% if ci == 'gitlab' %]gitlab-ci.yml[% endif %]`.
- Each tool has an exact version in `devkit.toml`, and each setting a comment saying why.
- A task in `devkit.toml` is one line; more than that is a script in `.config/mise/tasks/devkit/`, a
  hidden `devkit:*` task. Shell for a few commands, Python under `uv run --script`, stdlib only, for logic.
  A script is no template: what it needs from the answers comes from `[env]`, so it is one file in every
  project and the tests run it as it is.
- The project's ruff steps leave devkit's scripts out: devkit's own lint checks them, by its rules.

## A new step or question

1. the step in `template/.config/devkit/hk-steps.pkl.jinja`, behind its question if not every project wants it;
   its tool pinned in `devkit.toml.jinja`
2. the question in `copier.yml`, with a default that keeps existing projects as they are
3. a variant in `test.sh` that renders it and proves the step catches what it is for
4. the pages here: [Checks](Checks.md), [Setup](Setup.md#questions), a note in [Updating](Updating.md)

## Tests

`mise run test` runs both:

- `tests/test_cli.py`: the command, with fake mise and uwiki on PATH; doctor's edits check against a
  project rendered from this checkout
- `tests/test_tasks.py`: the scripts, with fake mise, uwiki and gitleaks on PATH
- `test.sh`: first devkit's own copies of the template's files against what the template renders, then the
  template rendered as projects, each linted with its own `mise run lint`:
  - **wiki:** the defaults; doctor finds a file of devkit's edited and one removed
  - **gitlab:** GitLab CI and wrap. A gitignored private page with a misspelling must fail lint, and pass
    once fixed; a key in an ignored `.env` must pass `devkit:leaks`, the same key in a file git sees must
    fail it.
  - **package:** `releases = python` with ruff; `devkit:version` reads the version file

Lint runs with no `devkit` on PATH, and no rendered file may run the command: a project needs none.

`test.sh` renders this checkout, changes not committed too: copier takes a dirty template's working tree.
It needs mise and uv. CI runs `mise run test` in `test.yml`, `mise run lint` in `lint.yml`.

## Trying a change

The command of this checkout runs anywhere as `uv run --project ~/prj/devkit devkit doctor`. In a project, `_src_path` in `.copier-answers.yml` set to this checkout, then `devkit update --to HEAD`
merges the template as it is here; `_src_path: gh:hiqdev/devkit` and the tag in `_commit` go back before a
commit. copier refuses a dirty project, so try it on a clone and move the diff over:
`git diff | git -C ../project apply`.

## Releasing devkit

1. a section in [Updating](Updating.md) for the release
2. `mise run minor`, or patch, major: runs `mise run test`, sets `__version__` in `src/devkit/__init__.py`,
   commits `vX.Y.Z` and tags it
3. `mise run release`: pushes master and the tag at once; `release.yml` tests again and creates the GitHub
   release, and `mise install pipx:hiqdev/devkit@vX.Y.Z` works anywhere
4. `mise run up`: the release on this machine, for `devkit init` in new projects

`devkit update` takes projects to the tag, so the tag has to be the reviewed content: tag the commit the
projects were tried with.
