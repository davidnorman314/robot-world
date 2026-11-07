"""A world with a river down the middle, a bridge, and a goal on the far bank."""

import random

from robot_api import Colors
from robot_world.world import Box, Patch, Pose, Rect, Terrain, World

WIDTH = 24.0
HEIGHT = 20.0
RIVER_WIDTH = 3.0
BRIDGE_WIDTH = 3.0  # across the deck, north to south
RAMP_LENGTH = 2.0  # how far the deck continues onto each bank, with no railing
RAIL_THICKNESS = 0.2
RAIL_HEIGHT = 0.6
WALL_THICKNESS = 0.3
WALL_HEIGHT = 1.0
GOAL_SIZE = 2.0
GOAL_POST_SIZE = 0.4
GOAL_POST_HEIGHT = 1.5
TIME_LIMIT = 180.0


def make_river_world(seed: int) -> World:
    """A river runs north to south across the middle of a fenced field, and the only
    way over it is a wooden bridge with railings. Your robot starts somewhere on the
    west bank, facing a random direction. Find the bridge, cross it, and drive onto the
    red goal square on the east bank. The red post in the middle of the goal can be
    seen from far away. Driving into the water ends the run."""
    rng = random.Random(seed)

    river_x0 = rng.uniform(9.0, 13.0)
    river = Rect(river_x0, 0.0, river_x0 + RIVER_WIDTH, HEIGHT)

    bridge_y0 = rng.uniform(3.0, HEIGHT - 3.0 - BRIDGE_WIDTH)
    bridge = Rect(
        river.x0 - RAMP_LENGTH, bridge_y0, river.x1 + RAMP_LENGTH, bridge_y0 + BRIDGE_WIDTH
    )

    goal_x0 = rng.uniform(river.x1 + 3.0, WIDTH - 2.0 - GOAL_SIZE)
    goal_y0 = rng.uniform(2.0, HEIGHT - 2.0 - GOAL_SIZE)
    goal = Rect(goal_x0, goal_y0, goal_x0 + GOAL_SIZE, goal_y0 + GOAL_SIZE)
    goal_cx, goal_cy = goal.center
    half = GOAL_POST_SIZE / 2
    goal_post = Rect(goal_cx - half, goal_cy - half, goal_cx + half, goal_cy + half)

    start = Pose(
        rng.uniform(2.0, river.x0 - 4.0), rng.uniform(2.0, HEIGHT - 2.0), rng.uniform(0, 360)
    )

    rails = (
        Rect(river.x0, bridge.y0 - RAIL_THICKNESS, river.x1, bridge.y0),
        Rect(river.x0, bridge.y1, river.x1, bridge.y1 + RAIL_THICKNESS),
    )
    walls = (
        Rect(0.0, 0.0, WIDTH, WALL_THICKNESS),
        Rect(0.0, HEIGHT - WALL_THICKNESS, WIDTH, HEIGHT),
        Rect(0.0, 0.0, WALL_THICKNESS, HEIGHT),
        Rect(WIDTH - WALL_THICKNESS, 0.0, WIDTH, HEIGHT),
    )

    return World(
        name=f"river-{seed}",
        width=WIDTH,
        height=HEIGHT,
        patches=(
            Patch(river, Terrain.WATER),
            Patch(bridge, Terrain.BRIDGE),
            Patch(goal, Terrain.GOAL),
        ),
        boxes=(
            *(Box(rail, RAIL_HEIGHT, Colors.RAILING) for rail in rails),
            *(Box(wall, WALL_HEIGHT, Colors.WALL) for wall in walls),
            Box(goal_post, GOAL_POST_HEIGHT, Colors.GOAL, solid=False),
        ),
        start=start,
        time_limit=TIME_LIMIT,
    )
