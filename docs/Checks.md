# Checks

`mise run lint`, the pre-commit hook and CI run the same steps, from `.config/devkit/hk-steps.pkl` and the
project's `hk.pkl`. `fail_fast = false` in `hk.pkl` has each step report, not the first failing one only.

## Pages

Over the pages `uwiki ls` lists, so a page `uwiki.toml` excludes is left out by each step:

| step | checks | rules |
|---|---|---|
| `uwiki` | links, headings, items, refs, images, front matter schema, list numbering: the whole vault, a link breaks from either end | `uwiki.toml` `[check]` |
| `markdownlint` | heading order, list style, fences, blank lines | `.markdownlint.yaml`, extending `.config/devkit/markdownlint.yaml` |
| `typos` | misspellings typos knows for sure | `_typos.toml` for jargon |
| `vale` | prose mistakes, proselint, and the case of the project's words | `.vale.ini`, the Wiki vocabulary |
| `wrap` | with `wrap`: paragraphs and list items wrapped at uwiki's width | `uwiki.toml` `[wrap]` |

devkit's markdownlint base turns off what is taste or another step's: line length (wrap's), blank lines
around headings and lists, a first-line heading (front matter has the title), list numbers (uwiki's) and table
column style. Vale runs proselint, no style guide: it leaves semicolons and the passive voice alone; spelling
is typos'.

## Every file

| step | checks |
|---|---|
| `trailing-whitespace`, `newlines`, `mixed-line-ending`, `byte-order-marker` | hygiene: no trailing blanks, one final newline, one line ending, no BOM |
| `merge-conflict` | no conflict markers left |
| `case-conflict` | no names differing only in case: one file on macOS and Windows |
| `symlinks` | no broken symlinks |
| `shellcheck` | shell scripts |
| `gitleaks` | no secrets in the files git sees, see [secrets](#secrets) |

## Code

With `python`: `ruff` (`ruff check`) and `ruff-format` (`ruff format --check`) over `*.py` and `*.pyi`, by the
rules of `.config/devkit/ruff.toml`: 120 columns, and B, I, UP and SIM on top of ruff's own. The project's
`pyproject.toml` extends it and adds its rules:

```toml
[tool.ruff]
extend = ".config/devkit/ruff.toml"
```

Without that, ruff takes `~/.config/ruff` on a laptop and its defaults in CI, and the two disagree;
`devkit doctor` notes it. Other languages are the project's steps, see
[A project's own](Customizing.md#its-own-steps).

## Files lint takes

`mise run lint` is `mise run -q devkit:files | hk check --files0-from -`: the files git sees, tracked and untracked but not
ignored, and the pages uwiki reads, ignored or not. A private folder is gitignored on purpose and still
rendered, so it is checked too. Each step then takes the files its glob matches, less the `hk.pkl` excludes.

Deleted files and submodules are left out.

## The hook

`mise run hooks` installs a git pre-commit hook running the steps over the staged files, with two changes:

- `gitleaks` scans the staged changes: `gitleaks git --pre-commit --staged`
- `large-files` fails on a file added over 500 kB; only here, as files committed earlier were meant to be

The hook never rewrites a file: it fails, `mise run fix` fixes, the commit goes again. `git commit --no-verify`
skips it, CI then catches what it would have.

## Fix

`mise run fix` runs the steps that can fix: markdownlint, the hygiene steps, wrap, ruff, and the project's steps
with a `fix`; the others check. typos only reports: a "correction" inside a code span or a table renames an
identifier (`is_payed` to `is_paid`), so a person makes it.

## On demand

- `mise run links`: lychee checks external links over the pages, by `.config/devkit/lychee.toml`. A dead link
  is someone else's server, so no commit waits for it: run it by hand or on a schedule.
- `mise run secrets`: gitleaks over the whole git history, a leak stays there after its fix.

## Secrets

The `gitleaks` step is `devkit:leaks`: gitleaks over the working tree, allowing what git ignores. A local
`.env` or a private folder is no leak, a key in a new untracked file is. `gitleaks dir` alone reads ignored
files, `node_modules` excepted. `.gitleaks.toml`, when the project has one, adds rules and allowlists:
devkit:leaks extends it.
