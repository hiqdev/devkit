# devkit

Standard tasks for my projects, the same in each: lint, fix, links, secrets, hooks and releases.
[mise](https://mise.jdx.dev) pins the tools and runs the tasks, [hk](https://hk.jdx.dev) runs the checks,
[copier](https://copier.readthedocs.io) copies them into a project and merges later changes in.
A project then runs on its own files, mise and hk: no devkit installed in it. The `devkit` command sets
it up and keeps it up to date:

```sh
mise use -g pipx:hiqdev/devkit   # once per machine
devkit init                      # new project: a few questions, then the tools and the hook
devkit update                    # later: merges devkit changes in, keeping the project's own lines
devkit doctor                    # what keeps lint or the hook from running, what is edited or out of date
mise run lint                    # every check, as CI and the pre-commit hook run them
mise tasks                       # the project's tasks, devkit's among them
```

The [docs](docs/README.md) tell everything: [concepts](docs/Concepts.md), [setup](docs/Setup.md),
[commands](docs/Commands.md), [checks](docs/Checks.md), [a project's own](docs/Customizing.md),
[CI](docs/CI.md), [releases](docs/Releases.md), [updating](docs/Updating.md),
[troubleshooting](docs/Troubleshooting.md), [development](docs/Development.md).
