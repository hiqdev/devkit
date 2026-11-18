# Releases

With `releases = python`, devkit releases a Python package whose version is `__version__ = "X.Y.Z"` in
`version_file`, tagged `vX.Y.Z`, installed with mise from GitHub:

```sh
mise run patch         # or minor, major: runs the test task, bumps, commits "vX.Y.Z" and tags it
mise run release       # pushes the branch and the tag at once; CI creates the GitHub release
mise run up            # installs the release with mise and checks the command's --version
```

Each task is a line of `devkit.toml` running a shell script in `.config/mise/tasks/devkit/`, which takes
`version_file`, `branch`, `package` and `command` from `devkit.toml` `[env]`.

- **patch**, **minor**, **major** run `devkit:bump`: it refuses a dirty tree, then runs `mise run test`:
  `mise.toml` defines it, devkit writes a placeholder that fails until it does.
- **release** refuses a HEAD not tagged with the version, then runs `git push --atomic origin BRANCH vX.Y.Z`:
  the branch and the tag land together or not at all.
- **up** runs `mise install PACKAGE@vX.Y.Z` and `mise prune` of older ones, then checks that the command a shell
  outside the project gets says `COMMAND X.Y.Z`. A just pushed tag installs at once, no wait for GitHub's
  release list.
- **clean** removes `dist`, `build` and `__pycache__`; `mise run devkit:version` prints the version.

With `ci = github`, `.github/workflows/release.yml` runs on a pushed `v*` tag: the test task with the tools
mise pins, then `gh release create` with generated notes. A project keeps its own test matrix, as uwiki's
`test.yml` over Python 3.11 to 3.14.
