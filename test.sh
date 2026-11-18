#!/bin/sh
# devkit applied to itself: its copies of the template's files are what the template renders from its answers
# (mise run self renders them). Then renders the template as projects, checks each renders configs mise and hk
# take and passes its own lint:
#   wiki      the defaults, GitHub CI
#   gitlab    GitLab CI and wrap; a gitignored private page lint must see: it fails until the page is fixed
#   package   a released Python package with ruff
# Lint and the devkit:* tasks run with no devkit command on PATH: a project needs none. devkit doctor is
# this checkout's. Needs mise and uv.
set -eu
cd "$(dirname "$0")"
here=$PWD
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

# PATH without the folders that have a devkit command, this checkout's .venv/bin among them
bare=$(printf %s "$PATH" | tr : '\n' | while read -r d; do [ -x "$d/devkit" ] || printf '%s:' "$d"; done)
bare=${bare%:}
dk() { uv run -q --project "$here" devkit "$@"; }
at() { dir=$tmp/$1; shift; (cd "$dir" && PATH=$bare "$@"); }

echo "--- self"
uvx -q copier copy -q --trust --defaults --vcs-ref HEAD --data-file .copier-answers.yml . "$tmp/self" >/dev/null
own=$(sed -n '/^_skip_if_exists:/,/^[^ ]/s/^  - \/\{0,1\}\([^ ]*\).*/\1/p' copier.yml)
stale=$(cd "$tmp/self" && find . -type f ! -name .copier-answers.yml | sed 's|^\./||' | sort | while read -r f; do
    echo "$own" | grep -qxF "$f" || cmp -s "$f" "$here/$f" || echo "$f"
done)
[ -z "$stale" ] || { printf 'not as the template renders them, mise run self:\n%s\n' "$stale" >&2; exit 1; }

render() {
    dir=$tmp/$1
    shift
    uvx -q copier copy --trust --defaults --vcs-ref HEAD "$@" "$here" "$dir" >/dev/null
    git -C "$dir" init -q
    printf '# Home\n\nSee [[Notes]].\n' > "$dir/index.md"
    printf '# Notes\n\nBack [[index|home]].\n' > "$dir/Notes.md"
    git -C "$dir" add -A
    (cd "$dir" && mise trust -q mise.toml && mise trust -q .config/mise/conf.d/devkit.toml && mise install -q)
}

lint() {
    at "$1" sh -c 'mise run -q lint >lint.log 2>&1'
}

check() {
    echo "--- $1"
    # devkit's files run mise tasks and scripts, never the devkit command
    if grep -rnE '(run|check) = "devkit ' "$tmp/$1" --exclude-dir=.git; then
        echo "$1 runs the devkit command" >&2
        exit 1
    fi
    if ! at "$1" mise x -- hk validate || ! lint "$1"; then
        cat "$tmp/$1/lint.log" >&2
        exit 1
    fi
}

render wiki
grep -q 'pipx:hiqsol/uwiki' "$tmp/wiki/mise.toml"
check wiki
# check is lint and test: a project without tests passes, warned there are none
at wiki sh -c 'mise run -q check >check.log 2>&1' || { cat "$tmp/wiki/check.log" >&2; exit 1; }
grep -q 'No tests' "$tmp/wiki/check.log" || { echo 'check did not warn of no tests' >&2; exit 1; }
# doctor: devkit's files as the template renders them, then one edited and one removed
dk_doctor() { (cd "$tmp/wiki" && dk doctor --offline) || true; }
dk_doctor | grep -E 'edited|missing' && { echo 'doctor found drift in a fresh project' >&2; exit 1; }
printf '# edited\n' >> "$tmp/wiki/.config/devkit/lychee.toml"
rm "$tmp/wiki/.config/devkit/markdownlint.yaml"
out=$(dk_doctor)
if ! echo "$out" | grep -q 'lychee.toml edited' || ! echo "$out" | grep -q 'markdownlint.yaml missing'; then
    printf 'doctor missed the drift:\n%s\n' "$out" >&2
    exit 1
fi
(cd "$tmp/wiki" && git checkout -q -- .config/devkit)

render gitlab -d ci=gitlab -d wrap=true
uvx -q --with pyyaml python -c 'import sys, yaml; yaml.safe_load(open(sys.argv[1]))' \
    "$tmp/gitlab/.config/devkit/gitlab-ci.yml"
[ ! -e "$tmp/gitlab/.github" ]
check gitlab
# a gitignored page uwiki renders: lint sees it, a misspelling there fails it
printf 'private/\n' > "$tmp/gitlab/.gitignore"
mkdir "$tmp/gitlab/private"
printf '# Private\n\nTeh page, back [[index|home]].\n' > "$tmp/gitlab/private/Private.md"
printf '# Home\n\nSee [[Notes]] and [[Private]].\n' > "$tmp/gitlab/index.md"
git -C "$tmp/gitlab" add .gitignore index.md
if lint gitlab; then echo 'lint missed the ignored page' >&2; exit 1; fi
grep -q 'private/Private.md' "$tmp/gitlab/lint.log" || { cat "$tmp/gitlab/lint.log" >&2; exit 1; }
printf '# Private\n\nThe page, back [[index|home]].\n' > "$tmp/gitlab/private/Private.md"
check gitlab
# a local .env is no leak, the same key in a file git sees is
printf 'GITHUB_TOKEN=ghp_1a2B3c4D5e6F7g8H9i0JkLmNoPqRsTuVwXyZ12\n' > "$tmp/gitlab/.env"   # gitleaks:allow, a fake
printf '.env\nprivate/\n' > "$tmp/gitlab/.gitignore"
at gitlab sh -c 'mise run -q devkit:leaks >/dev/null 2>&1' || { echo 'devkit:leaks flagged the ignored .env' >&2; exit 1; }
cp "$tmp/gitlab/.env" "$tmp/gitlab/config.txt"
if at gitlab sh -c 'mise run -q devkit:leaks >/dev/null 2>&1'; then echo 'devkit:leaks missed config.txt' >&2; exit 1; fi
rm "$tmp/gitlab/config.txt" "$tmp/gitlab/.env"

render package -d releases=python -d python=true -d version_file=src/pkg/__init__.py \
    -d package=pipx:example/pkg -d command=pkg
mkdir -p "$tmp/package/src/pkg"
printf '__version__ = "0.1.0"\n' > "$tmp/package/src/pkg/__init__.py"
git -C "$tmp/package" add -A
[ "$(at package mise run -q devkit:version)" = 0.1.0 ] && [ -e "$tmp/package/.github/workflows/release.yml" ]
[ ! -e "$tmp/wiki/.config/mise/tasks/devkit/bump.sh" ]   # release scripts only where releases is python
check package
# a package's check fails until mise.toml defines its tests
if at package sh -c 'mise run -q check >check.log 2>&1'; then echo 'check passed a package with no tests' >&2; exit 1; fi
printf '\n[tasks.test]\nrun = "true"\n' >> "$tmp/package/mise.toml"
at package sh -c 'mise run -q check >check.log 2>&1' || { cat "$tmp/package/check.log" >&2; exit 1; }
echo ok
