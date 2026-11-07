"""A river with three bridges, two of them broken in the middle."""

import random

from robot_world.world import Patch, Terrain, World
from robot_world.worlds import river as pieces

TIME_LIMIT = 360.0
# Each bridge's south edge is picked from its own band, so the three never overlap and
# there is always clear bank between them.
BRIDGE_BANDS = ((2.5, 4.0), (8.5, 10.0), (14.5, 16.0))


def make_three_bridges_world(seed: int) -> World:
    """The same river and fenced field as one-bridge, but now there are three bridges
    and two of them are broken: a piece is missing from the middle, over the water.
    From the bank the bridges all look alike, so your robot has to get close and look
    along each one to see which is whole. Start on the west bank, find the good
    bridge, cross it, and drive onto the red goal square on the east bank. Driving into
    the water, including the gap in a broken bridge, ends the run."""
    rng = random.Random(seed)
    river = pieces.make_river(rng)
    bridge_y0s = [rng.uniform(low, high) for low, high in BRIDGE_BANDS]
    whole = rng.randrange(len(bridge_y0s))
    bridge_patches: list[Patch] = []
    railings = []
    for index, y0 in enumerate(bridge_y0s):
        patches, boxes = pieces.make_bridge(river, y0, broken=index != whole)
        bridge_patches += patches
        railings += boxes
    goal, goal_post = pieces.make_goal(rng, river)
    start = pieces.make_start(rng, river)

    return World(
        name=f"three-bridges-{seed}",
        width=pieces.WIDTH,
        height=pieces.HEIGHT,
        patches=(Patch(river, Terrain.WATER), *bridge_patches, goal),
        boxes=(*railings, *pieces.make_walls(), goal_post),
        start=start,
        time_limit=TIME_LIMIT,
    )
