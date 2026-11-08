"""A fenced field with nothing in it but the goal: the first world."""

import random

from robot_world.world import Patch, Pose, Rect, Terrain, World
from robot_world.worlds import river as pieces

TIME_LIMIT = 120.0
MIN_DISTANCE = 8.0  # the goal is never closer than this to the start
MARGIN = 2.0  # keep the goal and the start away from the fence


def make_simple_goal_world(seed: int) -> World:
    """A fenced field of grass with a red goal square somewhere in it. The tall red post
    in the middle of the goal can be seen from anywhere in the field. Your robot starts
    somewhere else in the field, facing a random direction. Turn until you can see the
    goal, then drive onto it."""
    rng = random.Random(seed)
    x0 = rng.uniform(MARGIN, pieces.WIDTH - MARGIN - pieces.GOAL_SIZE)
    y0 = rng.uniform(MARGIN, pieces.HEIGHT - MARGIN - pieces.GOAL_SIZE)
    goal = Rect(x0, y0, x0 + pieces.GOAL_SIZE, y0 + pieces.GOAL_SIZE)
    gx, gy = goal.center
    while True:
        start = Pose(
            rng.uniform(MARGIN, pieces.WIDTH - MARGIN),
            rng.uniform(MARGIN, pieces.HEIGHT - MARGIN),
            rng.uniform(0, 360),
        )
        if (start.x - gx) ** 2 + (start.y - gy) ** 2 >= MIN_DISTANCE**2:
            break

    return World(
        name=f"simple-goal-{seed}",
        width=pieces.WIDTH,
        height=pieces.HEIGHT,
        patches=(Patch(goal, Terrain.GOAL),),
        boxes=(*pieces.make_walls(), pieces.make_goal_post(goal)),
        start=start,
        time_limit=TIME_LIMIT,
    )
