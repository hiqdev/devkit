# Updating

```sh
devkit update                 # to the latest tag
devkit update --to v0.3.0     # to a tag or a commit
devkit update -d wrap=true    # and change an answer
```

On a clean tree, as copier refuses a dirty one. It merges the template's changes between the project's
release and the new one into devkit's files, three ways: a line the project changed stays when devkit did
not change it too. Then `mise install` fetches the new pins. It prints the compare link of the two releases
and the files left with conflict markers.

Run the latest `devkit`, `mise up pipx:hiqdev/devkit`: it is the one that knows how to update to the
latest template. The project pins no devkit, so nothing in it holds an older one back.

1. `git diff` and the compare link: what changed
2. resolve each `<<<<<<<` conflict; one in a file devkit owns usually takes devkit's side, the project's
   change belongs in its own file
3. `devkit doctor`, `mise run check`
4. commit, `devkit vX.Y.Z` as the message

copier never writes the project's files on update: a change devkit's release notes ask for there is made by
hand, as the 0.3.0 notes below tell.

## 0.3.3

- **GitLab `.devkit-check`:** lint with its JUnit report, then the project's `test` task; both run, the job
  fails when either does. `.devkit-lint` stays, lint alone: a project with tests extends `.devkit-check`.
- **release says why it refuses:** a version with no tag yet takes `git tag vX.Y.Z` when it was set by hand,
  a tag on another commit takes a new version.

## 0.3.2

- **`check` is every check:** `lint` and `test`. CI, `patch` and the release workflow run it, so a lint
  failure stops a release before its tag. `test` is the project's, in `mise.toml`; devkit's warns there are
  no tests, or fails with Python. A project's own task named `check` overrides devkit's: rename it.
- **`.github/workflows/check.yml` replaces `lint.yml`:** copier removes `lint.yml`. A project's own
  `test.yml` stays, a test matrix for one.
- **ruff rules in `.config/devkit/ruff.toml`**, with `python`: 120 columns, B, I, UP, SIM. Add
  `extend = ".config/devkit/ruff.toml"` to `pyproject.toml` `[tool.ruff]` by hand, `devkit doctor` notes it
  until then; the project's own ruff rules stay there, on top.
- **`.config/devkit/AGENTS.md` updates:** copier skipped it as the project's `AGENTS.md`; now only the
  project root's is the project's.

## 0.3.1

- **A fresh uwiki installs:** `devkit.toml` exempts `pipx:hiqsol/uwiki` from mise's 24h
  `minimum_release_age`, so CI takes a uwiki release the day the project pins it.

## 0.3.0

- **The project runs on its own files:** the tasks run scripts in `.config/mise/tasks/devkit/`, hidden
  `devkit:*` mise tasks, with the answers they need in `devkit.toml` `[env]`. No devkit is installed in a
  project; the `devkit` command, from this repo, sets up, updates and checks. `tasks.sh` is gone: the
  release tasks run `devkit:bump`, `devkit:release`, `devkit:up`; `clean` is a task, the version is
  `mise run devkit:version`.
- **Agents:** `.config/devkit/AGENTS.md` tells them the tasks and who owns which file; a new project's
  `AGENTS.md` points there, an existing one adds a line that does.
- **doctor finds devkit's files edited**, which the next update would undo.
- **uwiki is the project's:** `mise.toml` pins it, `devkit update` moves the pin there from the answers.
  Bump with `mise use pipx:hiqsol/uwiki@X`; 0.30.0 or later.
- **Lint takes the pages uwiki reads**, gitignored private ones too: `devkit:files`. A private folder may
  have findings no check saw before.
- **gitleaks over what git sees:** `devkit:leaks`, a local `.env` is no leak.
- **New questions:** `ci = gitlab` with the hidden jobs, `wrap`, `python`.
- **typos no longer fixes:** it renamed identifiers in code spans.
- markdownlint MD029 and MD060, Vale `proselint.Very` off in devkit's base: a project's `.markdownlint.yaml`
  can drop its own lines for them.
- `release.yml` with `releases = python` and `ci = github`.

## 0.2.1

Vale ignores phrases wrapped across lines too.

## 0.2.0

Large files checked at pre-commit only, files committed earlier were meant to be; `proselint.But` off.

## 0.1.0

The template: lint and release tasks, mise pins the tools, hk runs the checks over the pages `uwiki ls` lists.
