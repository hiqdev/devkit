# CI

CI runs `mise run check`, lint and the project's tests, with the tools at the versions the project pins: what
passes locally passes there.

## GitHub

`ci = github`: `.github/workflows/check.yml` runs `mise run check` on a push to master or main and on each pull
request, with [mise-action](https://github.com/jdx/mise-action) installing the tools. It is devkit's, so it needs
nothing from the project. With `releases = python` there is `release.yml` too, see [Releases](Releases.md).

## GitLab

`ci = gitlab`: `.config/devkit/gitlab-ci.yml` holds hidden jobs, which run nothing by themselves. The project's
`.gitlab-ci.yml` stays its own: it includes the file and names the jobs it wants, with its stages, rules and
runner tags:

```yaml
include:
  - local: .config/devkit/gitlab-ci.yml

lint:
  extends: .devkit-lint
  stage: test
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH

links:                                     # on a schedule, never a gate
  extends: .devkit-links
  rules:
    - if: $CI_PIPELINE_SOURCE == "schedule"
```

| job | runs |
|---|---|
| `.devkit` | the base: `jdxcode/mise` image, git, the mise configs trusted, `mise install`, the tools on PATH |
| `.devkit-lint` | `mise run lint` with a JUnit report: each hk step shows in the merge request |
| `.devkit-links` | `mise run links`: external links, for a schedule |
| `.devkit-secrets` | `mise run secrets`: gitleaks over the whole history, `GIT_DEPTH: 0` |

A step that needs the project's own tools gets them in its job: the tools mise pins are on PATH after
`.devkit`'s `before_script`, so a job's `script` can run `npm ci` before devkit's:

```yaml
lint:
  extends: .devkit-lint
  script:
    - npm ci
    - !reference [.devkit-lint, script]
```

The tools are cached in `.cache/mise` inside the project, keyed on `devkit.toml` and `mise.toml`: a pin change
fetches again. A cold cache needs the runner to reach GitHub, npm and PyPI. `.cache/` goes to
`.git/info/exclude`, so lint does not take the tools for files.

## A job by hand

The lint job runs on a laptop with Docker, in the image the jobs use. It runs as root and writes into the
project, the tools and Vale's styles, so it takes a clone:

```sh
git clone -q . /tmp/ci && docker run --rm -v /tmp/ci:/builds/p -w /builds/p jdxcode/mise:2026.11.9-debian sh -c '
  git config --global --add safe.directory /builds/p
  export MISE_DATA_DIR=/builds/p/.cache/mise MISE_YES=1 && echo /.cache/ >> .git/info/exclude
  mise trust -q mise.toml && mise trust -q .config/mise/conf.d/devkit.toml && mise install -q
  mise run lint -- --junit-xml hk-junit.xml'
```

A clone has the committed files only: commit first, or copy the changed ones in. `docker run ... rm -rf
/builds/p/.cache` before removing the clone, its files are root's.
