# starter-bot

A robot program for [robot-world](../../README.md). All it does is drive in a square,
which usually ends badly. Copy this folder to start your own robot, and make it do better.
The easier way is the Claude Code prompt in the main README, which sets all of this up
for you; `CLAUDE.md` here is what it follows.

## Set it up

Install the `robot-world` command from GitHub at the tag David gave you:

```
uv tool install "git+https://github.com/davidnorman314/robot-world.git@v1.0.0#subdirectory=packages/robot-world"
```

`pyproject.toml` points at the same release tag (`tag = "v1.0.0"`). Change it only when
he says there is a new one. Then:

```
uv sync
```

## Update to a new tag

Run the install command again with the new tag and `--reinstall` added after `install`,
change the `tag` in `pyproject.toml` to match, then `uv sync` and `uv build --wheel`.

## Build it

```
uv build --wheel
```

That makes a file like `dist/starter_bot-0.1.0-py3-none-any.whl`. That file is your robot.

## Watch it

```
robot-world serve dist
```

This opens the viewer in your browser. Press Run. After you change the code, run
`uv build --wheel` again and press Run again.

## Run it without the browser

```
robot-world run dist/starter_bot-0.1.0-py3-none-any.whl
robot-world run dist/starter_bot-0.1.0-py3-none-any.whl --seed 7
robot-world run dist/starter_bot-0.1.0-py3-none-any.whl --episodes 10
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
