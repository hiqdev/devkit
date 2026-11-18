# Troubleshooting

`devkit doctor` finds most of it, and names the fix with each problem.

## What doctor reports

| doctor says | why | fix |
|---|---|---|
| `mise.toml untrusted` | mise ignores a config it does not trust, its tools and tasks are missing | `mise trust mise.toml` |
| `tools not installed` | a fresh clone, or a pin changed | `mise install` |
| `mise.toml pins no uwiki` | a project from before 0.3.0, or the line was dropped | `mise use pipx:hiqsol/uwiki@X` |
| `uwiki 0.29.0: the page steps need 0.30.0` | the page steps run `uwiki ls --only` | `mise use pipx:hiqsol/uwiki@X` |
| `core.hooksPath is .githooks` | git runs those hooks, hk's never | `git config --unset core.hooksPath`, `mise run hooks` |
| `no hk pre-commit hook` | a fresh clone: hooks are not cloned | `mise run hooks` |
| `mise tasks named like devkit commands` | `devkit NAME` runs the command | `mise run NAME`, or rename the task |
| `template v0.2.1, latest v0.3.0` | a newer devkit | `devkit update` |
| `.config/devkit/lychee.toml edited` | a change in a file of devkit's, the next update drops it | see [below](#doctor-says-a-file-of-devkits-is-edited) |
| `devkit 0.3.0 is older than the template v0.4.0` | this machine's command is behind the project | `mise up pipx:hiqdev/devkit` |

## Doctor says a file of devkit's is edited

doctor renders the template at the project's release, with its answers, and compares devkit's files. An
edited one loses its change on the next `devkit update`: move the change to the project's own file next to
it (`hk.pkl`, `mise.toml`, `.markdownlint.yaml`), or into the template, then `git checkout` devkit's file.
`template ... not rendered` means doctor could not fetch that release: offline, or a tag not pushed yet.

## Worktrees share the hook

A git worktree shares `.git/hooks` with its main checkout: `mise run hooks` in a worktree installs the hook for
the main checkout too, which may not have devkit's files yet, and then fails each commit there. Set devkit up
in a worktree with `devkit init --no-hooks`, and run `mise run hooks` in the main checkout once the branch is
merged.

## A step fails on a file it should not take

- A generated or data file: `exclude` in `hk.pkl`. A file trailing tabs are data in, a TSV with empty
  columns, belongs there: `mise run fix` would strip them.
- A page uwiki should not read at all: `exclude` in `uwiki.toml`.
- Why lint takes a gitignored file: uwiki reads it, see [Checks](Checks.md#files-lint-takes).

## typos misses `_typos.toml`

typos looks for its config from each file's real path: a page reached through a symlink into another tree
gets that tree's config, or none. Keep the vault's pages in the project, or name the config in the step
in `hk.pkl`:

```pkl
["typos"] { check = "uwiki ls -z . --only {{files}} | xargs -0 -r typos --config _typos.toml" }
```

## hk: cannot combine match_any with glob

devkit's `shellcheck` is hk's builtin, which picks files by `match_any`. A project giving it a `glob` sets
`match_any = null` as well, see [A project's own](Customizing.md#its-own-steps).

## mise.toml and devkit.toml pin one tool

mise takes `mise.toml`'s. That is how a project pins another version, and also how an old pin outlives a
devkit update: drop the `mise.toml` line when devkit's is as new.

## A local run passes, CI fails

- A file not committed: lint takes untracked files git does not ignore, CI has only what was pushed.
- A tool of the project's own the job lacks: see [CI](CI.md#gitlab).
- A Vale package fetched locally long ago: lint syncs packages only when missing, `vale sync` refetches.
