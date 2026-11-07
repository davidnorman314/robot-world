# river-bot

A robot program for [robot-world](../../README.md). It crosses the river by the bridge
and drives to the red goal. Copy this folder to start your own robot.

## Set it up

`pyproject.toml` points at a release tag of robot-world (`tag = "v0.1.0"`). Use the tag
David gave you, and change it only when he says there is a new one. Then:

```
uv sync
```

## Build it

```
uv build --wheel
```

That makes a file like `dist/river_bot-0.1.0-py3-none-any.whl`. That file is your robot.

## Run it

```
robot-world run dist/river_bot-0.1.0-py3-none-any.whl
robot-world run dist/river_bot-0.1.0-py3-none-any.whl --seed 7
robot-world run dist/river_bot-0.1.0-py3-none-any.whl --episodes 10
```

Every seed is a slightly different world: the river, the bridge, the goal and the
robot's starting spot all move. A robot that works on one seed might not work on
another, so try a few.

`robot-world check <wheel>` tells you whether a wheel is a valid robot program.

## How a robot program works

robot-world calls your `run(robot)` function once. The `robot` has these commands:

| Command | What it does |
| --- | --- |
| `robot.forward(meters)` | Drives straight ahead. Returns how far it really went (less if it bumped into something). |
| `robot.backward(meters)` | Drives straight back. |
| `robot.turn(degrees)` | Turns on the spot. Positive is left, negative is right. |
| `robot.look()` | Takes a picture and returns an `Image`. |
| `robot.heading()` | Which way the robot faces: 0 is east, 90 north, 180 west, 270 south. |
| `robot.say(text)` | Prints a message next to the robot's view, for debugging. |

The episode ends by itself when the robot reaches the goal, drives into water, or runs
out of time. You do not have to say you are done.

A picture is made of flat colors, one for each kind of thing. Compare pixels with the
constants in `Colors`: `SKY`, `LAND`, `WATER`, `BRIDGE`, `RAILING`, `GOAL`, `WALL`, `ROCK`.
Useful `Image` methods:

- `image.pixel(x, y)` gives the color at column `x`, row `y` (row 0 is the top).
- `image.count(color)` counts how many pixels have that color.
- `image.center(color)` gives the average `(x, y)` of that color, or `None` if it is
  nowhere in the picture. If `x` is less than `image.width / 2`, it is to the left.
- `image.mask(color)` gives a numpy array that is True where that color is.

The full API is in `robot_api`, which has docstrings for everything.

## Rules for a wheel

- Pure Python only. You may depend on `robot-api` and `numpy`, nothing else.
- Exactly one entry point in the `robot_world.robots` group, pointing at your `run`
  function. See `pyproject.toml`.
