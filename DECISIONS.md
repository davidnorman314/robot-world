# Decisions

Design decisions Claude made while building robot-world, for David to review. Each one
has a status: **proposed** (made by Claude, not yet reviewed), **accepted**, or
**changed** (with a note on what replaced it).

## 1. Local app with a browser front end - accepted

Each person runs the simulator locally with uv and opens a page on localhost. No hosted
server, no uploading wheels anywhere. The browser (three.js) only displays; the Python
simulator owns the world.

## 2. Turtle-style blocking robot API - accepted

Her program calls `robot.forward(1.0)`, `robot.turn(30)`, `robot.look()` in sequence.
The simulator advances simulated time inside each call. A step-style callback API can be
added later if she outgrows this.

## 3. The simulator renders the robot's camera on the CPU - accepted

A numpy ray-caster renders flat semantic colors (sky, land, water, bridge, goal, wall,
rock). Headless runs and tests see exactly the image her code sees, and runs are
deterministic for a seed. The browser shows the same image in a "robot eye" panel next to
its pretty rendering. Cost: the pretty view and the robot view are two renderers that
must agree on geometry.

## 4. Physics is 2.5D - accepted

The world is flat ground with rectangular terrain patches and axis-aligned boxes. The
robot is a circle with a pose (x, y, heading). No physics engine. 3D is presentation only.
Hills, ramps and non-rectangular shapes would need this revisited.

## 5. The goal has a tall post and the bridge has railings - accepted

From a camera 0.6 m above the ground, a flat 2 m patch 15 m away is under a pixel tall,
so the robot could not see where to go. The goal patch has a 1.5 m red post in its middle
(visible but not solid), and the bridge has 0.6 m railings in bridge color that also stop
the robot driving off the side. The bridge overhangs each bank by 0.5 m so the robot sees
bridge color under it before it is over water.

## 6. Looking costs 0.1 s of simulated time - accepted

A program that only looks still runs out the clock, and it roughly matches a real camera.
A wall-clock timeout in the runner catches programs that never call the robot at all.

## 7. Reaching the goal ends the episode automatically - accepted

The episode ends the moment the robot's centre enters the goal patch, by raising
`EpisodeOver` (a `BaseException`, so `except Exception` in her code does not swallow it).
She does not have to declare "done". Likewise entering water ends the episode as drowned.

## 8. Robot programs are wheels with an entry point, run in a subprocess - accepted

Her project declares `[project.entry-points."robot_world.robots"] name = "pkg:run"`.
The simulator adds the wheel to `sys.path` (pure-Python wheels import straight from the
zip) and finds `run` via `importlib.metadata`. The program runs in a subprocess so a new
wheel can be loaded without restarting, crashes are isolated, and a hung program can be
killed. Wheels must be pure Python and may depend only on `robot-api` and `numpy`.

## 9. Camera parameters - accepted

128x96 pixels, 90 degree horizontal field of view, eye 0.6 m up, pitched 10 degrees
down. Small enough that numpy renders it in a few milliseconds and her code can reason
about it; the viewer can upscale it.

## 10. Robot motion constants - accepted

Speed 1 m/s, turn 90 degrees/s, radius 0.3 m, tick 0.05 s. The one-bridge world is 24 x 20 m with
a 3 m river, a 3 m wide bridge deck with 2 m ramps, a 2 x 2 m goal, and a 180 s time limit.

## 11. Example robot depends on robot-api through `[tool.uv.sources]` - accepted

Hatchling refuses a direct git URL in `project.dependencies`. The template declares a
plain `robot-api` dependency and points `[tool.uv.sources]` at the repo's
`packages/robot-api` subdirectory, pinned to a release tag.

## 12. The example robot is a regression test for the world - accepted

`test_example_river_bot.py` runs the example on 20 seeds in-process (a 200-seed sweep
passed when it was written). If a world change breaks it, the world has become harder,
which should be a deliberate curriculum step, not an accident.

## 13. Releases are git tags, no PyPI - accepted

Tags are named `vX.Y.Z`. She pins `robot-api` and installs the simulator at a tag David
gives her, and stays there until he says to update, so he can keep working on `master`.
Both packages carry the same version as the tag.

## 14. 3D models come from CC0 packs and are vendored - accepted

The robot is Quaternius's Round Rover (Ultimate Space Kit, CC0), chosen by David. Model
files live under `static/models/` with their credits in `ATTRIBUTION.md` there, so the
viewer works offline and installs from the repo need nothing else. Models are
normalised at load time (measured, scaled to robot size, converted to z-up, set on the
ground) rather than hand-tuned, so swapping a model is a one-line change.

## 15. Solutions for later worlds live in the test suite, not in examples - accepted

`examples/river-bot` is her template and solves one-bridge, so its solution is public
by design. Each harder world also needs a program that solves it, so the world stays a
tested regression target, but putting that program in `examples/` would hand her the
answer. Those solver bots live in `packages/robot-world/tests/bots/` instead. They are
still in the public repo, just not presented as templates.

## 16. World names describe the puzzle - accepted

Worlds are named for what she has to deal with (`one-bridge`, `three-bridges`), not
numbered levels, so the names stay meaningful when worlds are added in between.

## 17. Batch runs stream summaries; a failed seed is replayed by running it again - accepted

The "Test many seeds" tab asks `POST /api/batch` for a range of seeds. The server runs
up to four episodes at a time (each program is its own subprocess anyway) and streams
one small JSON line per finished episode: seed, outcome, time, messages and error, but
no frames or pictures. Clicking a seed re-runs just that seed through `POST /api/run`
rather than fetching a stored recording. That keeps the batch cheap and the server
stateless, and it is exact because worlds and runs are deterministic for a seed; the
only caveat is that if the wheel was rebuilt in between, the replay uses the new wheel.

## 18. Worlds are listed easiest first, and the first one is the default - accepted

`WORLDS` is now an ordered curriculum rather than an alphabetical list, with
`simple-goal` (just a fenced field and the goal) at the front. The CLI, `robot-world
worlds` and the viewer's world menu all use that order, and the default world for
`run` and `serve` is whichever comes first, so a new player lands on the easiest world.
This moved the default from one-bridge to simple-goal; pass `--world one-bridge` or
pick it in the menu to get the old default.
