# robot-world

A virtual world where a tracked robot with a camera drives around to accomplish a goal.
You write the robot's program in Python, build it into a wheel, load it into the
simulator, and watch how it does. The worlds are randomly generated from a seed, so a
robot has to cope with the bridge, the goal and its own starting spot moving around.

The first world is a river with a bridge: the robot starts on one bank and has to cross
the bridge and drive to the red goal on the other bank.

## Install

You need [uv](https://docs.astral.sh/uv/). Then:

```
uv tool install git+https://github.com/davidnorman314/robot-world.git#subdirectory=packages/robot-world
```

That gives you the `robot-world` command.

## Write a robot

Copy [examples/river-bot](examples/river-bot) and follow its README. In short, a robot
program is a function:

```python
from robot_api import Colors, Robot


def run(robot: Robot) -> None:
    while True:
        image = robot.look()
        goal = image.center(Colors.GOAL)
        if goal is None:
            robot.turn(45)
        else:
            x, _ = goal
            robot.turn(-45 * (x - image.width / 2) / (image.width / 2))
            robot.forward(0.5)
```

The robot drives with `forward`, `backward` and `turn`, sees with `look`, and knows
which way it faces with `heading`. The camera image is flat colors, one per kind of
thing, so the program can tell land from water from bridge by comparing colors.

## Run a robot

```
uv build --wheel                                     # in your robot's folder
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
  simulation, wheel loading and the CLI.
- `examples/river-bot` is an example robot that solves the river world.

Design decisions are recorded in [DECISIONS.md](DECISIONS.md).
