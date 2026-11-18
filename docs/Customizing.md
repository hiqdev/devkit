# A project's own

A project changes devkit through its own files, never devkit's: `devkit update` rewrites those.

## Its tests

`mise run check` is `lint` and `test`. `test` is the project's: `mise.toml` defines it, and overrides devkit's,
which warns there are no tests, or fails with `python` or `releases = python`:

```toml
[tasks.test]
description = "the unit tests"
run = "uv run python -m unittest discover tests"
```

## Its own steps

In `hk.pkl`, in the mapping it hands `devkit.hooks`. A step of a new name is added, one of devkit's names
amends devkit's step:

```pkl
hooks = devkit.hooks((devkit.steps) {
  // a check of the project's own
  ["indexes"] {
    glob = List("**/*.md")
    check = "uwiki index --check docs"
  }
  // devkit's uwiki step, for two vaults
  ["uwiki"] { check = "uwiki check knowledge && uwiki check docs" }
  // devkit's shellcheck, over a list of the project's: a glob replaces the builtin's match_any
  ["shellcheck"] {
    match_any = null
    glob = List("ci/**/*.sh")
    check = "sh ci/checks/shellcheck.sh"
  }
})
```

- `glob` picks the files the step runs for, `{{files}}` in `check` names them; a check of the whole project
  ignores them, running when any matches.
- `fix` makes `mise run fix` run it; a step without one only checks.
- A step needing a tool of the project's, `npm run validate` after `npm ci`, gets the tool where CI runs too:
  see [CI](CI.md#gitlab).
- `mise run lint -- --skip-step vale` skips a step once, `--step typos` runs one alone. A step that does not
  fit for good wants the rule that does not fit turned off, see [rules and words](#rules-and-words).

## Files no step takes

`exclude` in `hk.pkl`, globs from the project root:

```pkl
exclude = List("data/snapshots/**", "tests/fixtures/**")
```

Pages to leave out of the vault itself, of the build too, go to `uwiki.toml` `exclude`: the page steps
follow it.

## Rules and words

- **markdownlint:** `.markdownlint.yaml` extends devkit's base; `MD033: false` allows inline HTML.
- **typos:** `_typos.toml`, a word typos takes for a misspelling is allowed under `[default.extend-words]`:
  `thr = "thr"`.
- **Vale:** a word of the project in `.vale/styles/config/vocabularies/Wiki/accept.txt`, one per line, a
  phrase a rule misreads in `.vale.ini` `TokenIgnores`; a rule off in `.vale.ini` under `[*.md]`:
  `proselint.Cliches = NO`. `.vale.ini` is merged on update, the project's lines stay.
- **gitleaks:** `.gitleaks.toml`, devkit:leaks extends it: `[[allowlists]]` for a test fixture.
- **lychee:** `.config/devkit/lychee.toml` is devkit's; a project needing other settings overrides the `lychee`
  step of the `links` hook in `hk.pkl`.

## Tools and versions

In `mise.toml`, which mise takes over `devkit.toml`:

- **uwiki:** `mise use pipx:hiqsol/uwiki@X`; 0.30.0 or later.
- **another version of a devkit tool:** pin it in `mise.toml`, `typos = "1.53.0"`. Drop the line when devkit
  catches up, or it stays behind.
- **the project's own tools:** `node`, `python`, as any mise project.

## Its own tasks

In `mise.toml`: `mise run NAME` runs them. One named like a task of devkit's (`lint`, `patch`) replaces
devkit's in this project: mise takes `mise.toml` over `devkit.toml`. One named like a devkit command
(`init`, `update`, `doctor`) is reached by `mise run` only, not `devkit NAME`; `devkit doctor` notes it.

## CI jobs

The GitHub workflow is devkit's. A GitLab project's `.gitlab-ci.yml` is its own and extends devkit's hidden
jobs, see [CI](CI.md).
