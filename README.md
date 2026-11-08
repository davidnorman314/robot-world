# robot-world

A virtual world where a tracked robot with a camera drives around to accomplish a goal.
You write the robot's program in Python, build it into a wheel, load it into the
simulator, and watch how it does. The worlds are randomly generated from a seed, so a
robot has to cope with the bridge, the goal and its own starting spot moving around.

The worlds so far, easiest first:

- **simple-goal**: a fenced field with nothing in it but the red goal. Turn until you
  see it, then drive to it.
- **one-bridge**: a river with a bridge. The robot starts on one bank and has to cross
  the bridge and drive to the red goal on the other bank.
- **three-bridges**: the same river with three bridges, two of them broken in the
  middle. From the bank they all look alike, so the robot has to go and look along each
  one before crossing.

`robot-world worlds` prints the full description of each.

## Install

You need [uv](https://docs.astral.sh/uv/). Then install the simulator at a release tag:

```
uv tool install "git+https://github.com/davidnorman314/robot-world.git@v0.2.0#subdirectory=packages/robot-world"
```

That gives you the `robot-world` command. To move to a newer release, run the same
command with the new tag. Releases are listed on the GitHub tags page.

## Write a robot

Copy [examples/starter-bot](examples/starter-bot) and follow its README. It includes a
`CLAUDE.md` that tells Claude Code to help you learn rather than solve the world for
you. In short, a robot program is a function:

```python
from robot_api import Robot


def run(robot: Robot) -> None:
    robot.say("Hello! I am going to drive in a square.")
    for side in range(4):
        robot.forward(10.0)
        robot.turn(90)
```

That one drives in a square and usually ends up in the river. The robot drives with `forward`, `backward` and `turn`, sees with `look`, and knows
which way it faces with `heading`. The camera image is flat colors, one per kind of
thing, so the program can tell land from water from bridge by comparing colors.

## Run a robot

Build the wheel in your robot's folder, then open the viewer:

```
uv build --wheel
robot-world serve dist
```

The viewer opens in your browser. Press Run to watch the robot drive, in a top-down,
chase, first-person or free orbit view. The panel on the right shows the exact picture
the program saw at each `look`, and the messages it said. Use the scrubber to go back
to the moment it went wrong. Rebuild the wheel and press Run again to try a change;
`serve dist` always picks the newest wheel in the folder.

A robot that works on one seed can fail on another, because the bridge, the goal and
the start move. The **Test many seeds** tab runs the wheel on a range of seeds, several
at a time, and lists how each one went, with the failed seeds called out. Click a row
to replay that seed in the Watch tab; worlds and runs are deterministic for a seed, so
you see the same run the test did.

To run without the browser, for quick checks or for many seeds at once:

```
robot-world run dist/my_robot-0.1.0-py3-none-any.whl --seed 1 --episodes 5
```

Each episode prints its outcome: `success`, `drowned`, `timeout`, `finished` (the
program returned without reaching the goal), `error` (it raised an exception) or
`stuck` (it stopped responding).

## Develop the simulator

```
uv sync
uv run pytest
uv run ruff check . && uv run ruff format .
```

The repo is a uv workspace:

- `packages/robot-api` is the small package robot programs import.
- `packages/robot-world` is the simulator: world model, world generators, camera,
  simulation, wheel loading, the CLI, and the browser viewer (a FastAPI server plus a
  vanilla three.js page in `static/`, with three.js vendored so there is no Node build).
- `examples/starter-bot` is the template robot project. It only drives in a square; the
  robots that solve each world live in `packages/robot-world/tests/bots/`.

## Release

Releases are git tags named `vX.Y.Z`. A robot project pins `robot-api` to a tag, and the
simulator is installed from a tag, so work on `master` never disturbs a robot that stays
on its tag. To cut a release: set the same version in both `packages/*/pyproject.toml`,
commit, then `git tag vX.Y.Z` and `git push --tags`.

## Credits

The robot is the Round Rover from Quaternius's Ultimate Space Kit (CC0). Model credits
are listed in `packages/robot-world/src/robot_world/static/models/ATTRIBUTION.md`. The
viewer uses [three.js](https://threejs.org) (MIT), vendored under `static/vendor/`.

Design decisions are recorded in [DECISIONS.md](DECISIONS.md).
