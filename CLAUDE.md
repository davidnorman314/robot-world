# robot-world

A 3D virtual world where a tracked robot with a camera drives around to accomplish a
goal. David builds the simulator and the worlds. His granddaughter (11, learning Python,
uses Claude Code on a Mac) writes robot programs as wheels, loads them into the app,
watches how her robot does, and iterates. Worlds get harder over time as her skills grow.

## Layout

- `packages/robot-api` - `robot_api`, the only package a robot program imports. Keep it
  small, pure Python, and documented well enough that Claude Code can write a robot from
  the docstrings alone. Changing it is an API change for her code.
- `packages/robot-world` - `robot_world`, the simulator: world model, world generators,
  camera, simulation, wheel loading, CLI, and (later) the browser viewer.
- `examples/` - example robot projects; `river-bot` doubles as her template. Its
  `CLAUDE.md` is written for Claude Code in *her* project (be a teacher, do not solve
  the world for her); it is not instructions for working on the simulator.
- `DECISIONS.md` - design decisions Claude makes that David should review.

## Commands

- `uv sync` - create or update `.venv` (Python 3.12).
- `uv run pytest` - all tests.
- `uv run ruff check . && uv run ruff format .` - lint and format.
- `uv run robot-world --help` - the simulator CLI.

If `uv sync` was run before a package's source existed, reinstall it with
`uv sync --reinstall-package <name>` or imports fail.

## Workflow (overrides the global rule against committing)

- Claude makes the commits in this repo. Keep them small and well organised, one unit of
  work each, conventional commits format, no `Co-Authored-By` line.
- TDD: write the failing test first, then the production code. Every production commit
  includes its tests.
- Trunk-based: commit to `master`, no feature branches.
- Pause and ask David when a decision needs his input. Record decisions he should review
  in `DECISIONS.md` as they are made.
- Keep `README.md` current with every change to commands, the robot API or the layout.
- Never use `from __future__ import annotations`.

## Releases

Releases are git tags `vX.Y.Z`. Her robot project pins `robot-api` to a tag and she
installs the simulator from a tag, so `master` can move freely. When David asks for a
release: set the same version in `packages/robot-api/pyproject.toml` and
`packages/robot-world/pyproject.toml`, commit, and create the tag. Claude creates tags;
David pushes them. Ask David whether to cut a release at natural points, such as when a
feature she would use is complete, but never tag without being asked. Breaking changes
to `robot_api` need a minor version bump and a note in the release so she knows what to
change.

## Design rules

- The simulator owns the world and renders the robot's camera itself (numpy ray-caster,
  flat semantic colors). The browser only displays. Headless runs must be deterministic
  given a seed.
- The robot program API is turtle-style and blocking: `forward`, `backward`, `turn`,
  `look`, `heading`, `say`. The episode ends on its own (goal, water, timeout).
- Robot programs are pure-Python wheels exposing a `run(robot)` entry point in the
  `robot_world.robots` group. They run in a subprocess.
- Everything the robot can see has its own color in `Colors`. Never give two different
  kinds of thing the same color; a robot program tells them apart only by color.
