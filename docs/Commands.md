# Commands

A project's tasks are mise's: `mise tasks` lists them, `mise run TASK` runs one. The `devkit` command sets
devkit up in a project, updates and checks it; `devkit TASK` runs a mise task too. `devkit` without a
command lists its commands and the project's tasks, `devkit COMMAND --help` a command's options.

## Commands of devkit

| command | does |
|---|---|
| `devkit init` | copies devkit into the project and sets it up, see [init](#init) |
| `devkit update` | merges a newer devkit in, see [Updating](Updating.md) |
| `devkit doctor` | what keeps lint or the hook from running, what is edited or out of date, see [doctor](#doctor) |
| `devkit TASK` | any other word runs `mise run TASK`, the arguments after it too |

## Tasks

devkit's tasks, in `devkit.toml`. A task of the same name in `mise.toml` overrides devkit's.

| task | does |
|---|---|
| `check` | every check: `lint` and `test`, as CI, `patch` and the release workflow run them |
| `test` | the project's tests, which `mise.toml` defines; devkit's warns there are none, or fails with Python |
| `lint` | the checks over the files lint takes, see [Checks](Checks.md) |
| `fix` | fixes what markdownlint, the hygiene steps, wrap and ruff can, then checks the rest |
| `links` | external links alive with lychee: other people's servers, on demand |
| `secrets` | gitleaks over the whole git history: a leak stays there after its fix |
| `hooks` | installs the git pre-commit hook: lint over the staged files, rewriting nothing |
| `patch`, `minor`, `major`, `release`, `up`, `clean` | with `releases = python`, see [Releases](Releases.md) |

Arguments after `--` reach hk: `mise run lint -- --junit-xml hk.xml`, `mise run lint -- --step typos`.

## Helpers

The tasks run scripts in `.config/mise/tasks/devkit/`, as hidden mise tasks: `mise tasks --hidden` lists
them. They seldom need running by hand:

| helper | does |
|---|---|
| `devkit:files` | prints the files lint takes, NUL-separated: what git sees, and the pages uwiki reads, gitignored ones too; `mise run -q devkit:files \| xargs -0 ls` shows them |
| `devkit:leaks [GITLEAKS OPTIONS]` | `gitleaks dir` over the working tree, allowing what git ignores, with the rules of `.gitleaks.toml` when there is one |
| `devkit:version`, `devkit:bump PART`, `devkit:release`, `devkit:up` | with `releases = python`: what the release tasks run |

They take the answers they need from `devkit.toml` `[env]`: `DEVKIT_VAULT`, and with releases
`DEVKIT_VERSION_FILE`, `DEVKIT_BRANCH`, `DEVKIT_PACKAGE`, `DEVKIT_COMMAND`.

## init

`devkit init [-d KEY=VALUE]... [--defaults] [--ref REF] [--src SRC] [--no-hooks]`

1. copier copies the template at the tag of this devkit, `v` and its version, or `--ref`;
   `--src` takes another template, a local checkout for one
2. `mise trust` on both mise configs, `mise install`
3. `mise run hooks`, unless `--no-hooks` or a `core.hooksPath` rules git's hooks
4. lists what the project still has that devkit does now, see [Setup](Setup.md#a-project-with-its-own-lint)

It refuses a project with `.copier-answers.yml`: that one is on devkit, `devkit update` is next.

## doctor

`devkit doctor [--offline]` reads, changes nothing, exits 1 on a problem. Problems keep lint or the hook
from running as they should:

- a mise config not trusted: mise ignores it
- a tool not installed
- no uwiki pinned, or a uwiki before 0.30.0, which the page steps need
- `core.hooksPath` set: git runs those hooks, never hk's
- no hk pre-commit hook

Notes are what is out of date or odd:

- a file of devkit's edited or removed: doctor renders the template at the project's release with its
  answers and compares; the next `devkit update` rewrites the file, so the change belongs in the
  project's own file or in the template. `.vale.ini` is left out: it keeps the project's own lines
- what a project set up before devkit still has, as [init](#init) lists it
- this devkit older than the template release the project is on: `mise up pipx:hiqdev/devkit`
- a mise task named like a devkit command: the command wins, `mise run` reaches the task
- a Vale package not synced yet: lint syncs it
- neither `AGENTS.md` nor `CLAUDE.md` points to `.config/devkit/AGENTS.md`
- a newer devkit or uwiki release; `--offline` skips asking GitHub, and the edits check of a template
  that is not a local checkout
