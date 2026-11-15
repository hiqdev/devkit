#!/bin/sh
# Renders the template as a wiki project and as a released Python package, then checks each renders
# configs mise and hk take and passes its own lint. Needs mise and uv; fetches tools on the first run.
set -eu
cd "$(dirname "$0")"
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

render() {
    dir=$tmp/$1
    shift
    uvx -q copier copy --trust --defaults --vcs-ref HEAD "$@" . "$dir" >/dev/null
    git -C "$dir" init -q
    printf '# Home\n\nSee [[Notes]].\n' > "$dir/index.md"
    printf '# Notes\n\nBack [[index|home]].\n' > "$dir/Notes.md"
    git -C "$dir" add -A
    (cd "$dir" && mise trust -q mise.toml && mise trust -q .config/mise/conf.d/devkit.toml && mise install -q)
}

check() {
    echo "--- $1"
    (cd "$tmp/$1" && mise x -- hk validate && mise run -q lint >lint.log 2>&1) || { cat "$tmp/$1/lint.log" >&2; exit 1; }
}

render wiki
check wiki

render package -d releases=python -d version_file=src/pkg/__init__.py -d package=pipx:example/pkg -d command=pkg
mkdir -p "$tmp/package/src/pkg"
printf '__version__ = "0.1.0"\n' > "$tmp/package/src/pkg/__init__.py"
git -C "$tmp/package" add -A
(cd "$tmp/package" && [ "$(mise run -q version)" = 0.1.0 ] && mise x -- shellcheck .config/devkit/tasks.sh)
check package
echo ok
