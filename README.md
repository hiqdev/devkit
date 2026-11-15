# devkit

Lint and release tasks for my projects, the same in each:
[mise](https://mise.jdx.dev) pins the tools and runs the tasks, [hk](https://hk.jdx.dev) runs the checks,
[copier](https://copier.readthedocs.io) copies them into a project and later merges changes in.

```sh
uvx copier copy --trust gh:hiqdev/devkit .    # new project: answers a few questions
uvx copier update --trust                     # later: merges devkit changes, keeps the project's own lines
mise trust && mise install
mise run lint                                 # all checks, as CI and the pre-commit hook run them
mise run hooks                                # once per clone: pre-commit checks staged files
```

## Checks

`mise run lint`, the pre-commit hook and CI run the same steps:

- pages, as `uwiki ls` lists them so uwiki.toml excludes hold for each:
  uwiki check, markdownlint, typos, Vale with proselint
- every file: trailing whitespace, final newline, line endings, BOM, merge conflict markers,
  names differing only in case, broken symlinks, shellcheck, gitleaks for secrets
- pre-commit also: files added over 500 kB

On demand: `mise run links` checks external links with lychee, `mise run secrets` runs gitleaks over git history.
`mise run fix` fixes what markdownlint, typos and the hygiene steps can; the hook never rewrites.

## Releases

With `releases = python`: `mise run patch|minor|major` tests, bumps `__version__`, commits and tags,
`mise run release` pushes the branch and the tag at once for CI to publish, `mise run up` installs the release.

## Who owns what

| devkit's, `copier update` rewrites them | the project's, written once |
|---|---|
| `.config/devkit/`: hk steps, release tasks, lychee and base markdownlint config | `mise.toml`: its own tools and tasks |
| `.config/mise/conf.d/devkit.toml`: tools and tasks, mise merges it | `hk.pkl`: hk settings and its own steps |
| `.github/workflows/lint.yml` | `.markdownlint.yaml`: its rules on top of devkit's |
| `.vale.ini`, merged: the project's own lines stay | `.vale/styles/config/vocabularies/Wiki/`: its words |

## Questions

| | |
|---|---|
| `vault` | folder uwiki checks, `.` by default |
| `uwiki` | uwiki release the checks run, `checkout` in uwiki's own repo |
| `ci` | `github` or `none` |
| `releases` | `none` or `python`, then `version_file`, `package`, `command`, `branch` |

`sh test.sh` renders a wiki project and a Python package and runs their lint.
