# Concepts

## What devkit is

A [copier](https://copier.readthedocs.io) template and a small Python command, versioned by one tag.
The template writes the lint and release setup into a project: mise tasks, hk steps and the scripts
behind them. The command sets it up, updates it and checks it, and nothing else: a project lints,
hooks and releases with mise and hk alone, no devkit installed. Each project runs the same checks the
same way:

- locally: `mise run lint`, or `mise run lint`, which runs it
- before each commit: the git pre-commit hook hk installs, over the staged files
- in CI: a job running `mise run lint`, with the tools at the versions the project pins

## Layers

| layer | file | owner |
|---|---|---|
| tools | `.config/mise/conf.d/devkit.toml` `[tools]` | devkit |
| the wiki tool | `mise.toml` `"pipx:hiqsol/uwiki" = "X"`, seeded once | project |
| checks | `.config/devkit/hk-steps.pkl`: page, file and code steps, the hooks | devkit |
| tasks | lint, fix, links, secrets, hooks in `devkit.toml`; CI and the hook call them | devkit |
| scripts | `.config/mise/tasks/devkit/`: the `devkit:*` helpers the tasks run, hidden | devkit |
| answers the scripts take | `devkit.toml` `[env]`: `DEVKIT_VAULT`, the release ones | devkit |
| agents' guide | `.config/devkit/AGENTS.md`, which `AGENTS.md` points to | devkit |
| command | `devkit` init, update, doctor; installed once per machine, not in the project | devkit |
| CI | `.github/workflows/lint.yml`, `.config/devkit/gitlab-ci.yml` | devkit |
| the project's checks and tasks | `hk.pkl` steps, `mise.toml` tasks, `.gitlab-ci.yml` jobs | project |

[mise](https://mise.jdx.dev) merges `mise.toml` with `conf.d/devkit.toml`, and takes `mise.toml` where both pin
a tool. [hk](https://hk.jdx.dev) reads `hk.pkl`, which amends devkit's `hk-config.pkl` and takes devkit's steps
to add its own or change some.

## Who owns what

| devkit's: `devkit update` rewrites them | the project's: written once, never again |
|---|---|
| `.config/devkit/`: hk steps and settings, GitLab jobs, lychee and base markdownlint config | `mise.toml`: uwiki's version, its own tools and tasks |
| `.config/mise/conf.d/devkit.toml`: tools and tasks | `hk.pkl`: hk settings, excludes, its own steps |
| `.config/mise/tasks/devkit/`: the scripts behind the tasks | `AGENTS.md`: points agents to devkit's guide |
| `.github/workflows/lint.yml`, `release.yml` | `.markdownlint.yaml`: its rules on top of devkit's |
| `.vale.ini`, merged: the project's own lines stay | `.vale/styles/config/vocabularies/Wiki/`: its words |
| `.copier-answers.yml`: the answers and the template release | `_typos.toml`, `.gitleaks.toml`, `uwiki.toml` when it needs them |

A file devkit owns starts with `Managed by devkit`: a change there goes into the template, or it is lost on the
next update. copier merges an update into it, so a line the project added survives, but the place for it is
the project's file next to it.

## Rules devkit keeps

- **One implementation.** The mise tasks are the checks. `mise run lint`, CI and the hook run them, so a
  green `mise run lint` before a push means a green CI.
- **The project runs on its own files.** Lint, the hook, CI and releases run mise, hk and the scripts
  devkit wrote into the project. The `devkit` command sets up and updates, so no installed devkit can be
  missing or another version than the project's files.
- **The hook never rewrites.** It checks the staged files and fails; `mise run fix` fixes.
- **Checks take what gets rendered.** Page steps take the pages `uwiki ls` lists, so a page uwiki.toml
  excludes is skipped by each, and a gitignored page uwiki renders is checked by each.
- **Others' servers are no gate.** External links are checked on demand or on a schedule, not on commit.
- **Quiet unless wrong.** A rule stays on when a finding is a mistake, not a matter of taste:
  proselint, not a style guide; typos' sure misspellings, not a dictionary.
- **The project decides.** devkit's files give defaults, the project's files override them; devkit never
  writes a project's file twice.

## Why these tools

- **mise** pins every tool, from npm, PyPI, GitHub releases or its registry, in one file, and runs tasks:
  a laptop and CI get the same versions with one `mise install`.
- **hk** runs steps in parallel over the files that match each, and has the hygiene checks built in. Its Pkl
  config lets a project amend devkit's steps instead of copying them.
- **copier** merges template changes into rendered files, three ways, so devkit's changes reach a project
  that changed the same files.
- **Scripts in the project** do what is more than a line of `devkit.toml`: listing the files lint takes,
  the gitleaks config, the release steps. Shell where it is a few commands, Python under `uv run --script`
  where it is logic. They are the same file in every project, no templating: the answers they need come
  from `[env]`, so devkit's tests run them as they are, and a person or an agent reads them in place.
- **The command** holds what the project's files cannot: the steps before they exist, merging a newer
  template in, finding what is broken or edited. Run from the latest devkit, not the project's.
