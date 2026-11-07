"""A world with a river down the middle, one bridge, and a goal on the far bank."""

import random

from robot_world.world import Patch, Terrain, World
from robot_world.worlds import river as pieces

TIME_LIMIT = 180.0


def make_one_bridge_world(seed: int) -> World:
    """A river runs north to south across the middle of a fenced field, and the only
    way over it is a wooden bridge with railings. Your robot starts somewhere on the
    west bank, facing a random direction. Find the bridge, cross it, and drive onto the
    red goal square on the east bank. The red post in the middle of the goal can be
    seen from far away. Driving into the water ends the run."""
    rng = random.Random(seed)
    river = pieces.make_river(rng)
    bridge_y0 = rng.uniform(3.0, pieces.HEIGHT - 3.0 - pieces.BRIDGE_WIDTH)
    bridge_patches, railings = pieces.make_bridge(river, bridge_y0, broken=False)
    goal, goal_post = pieces.make_goal(rng, river)
    start = pieces.make_start(rng, river)

    return World(
        name=f"one-bridge-{seed}",
        width=pieces.WIDTH,
        height=pieces.HEIGHT,
        patches=(Patch(river, Terrain.WATER), *bridge_patches, goal),
        boxes=(*railings, *pieces.make_walls(), goal_post),
        start=start,
        time_limit=TIME_LIMIT,
    )
