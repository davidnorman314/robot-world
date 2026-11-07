"""Pieces shared by the river worlds: the river, bridges, goal, start pose and fence."""

import random

from robot_api import Colors
from robot_world.world import Box, Patch, Pose, Rect, Terrain

WIDTH = 24.0
HEIGHT = 20.0
RIVER_WIDTH = 3.0
BRIDGE_WIDTH = 3.0  # across the deck, north to south
RAMP_LENGTH = 2.0  # how far the deck continues onto each bank, with no railing
GAP_WIDTH = 1.2  # the missing piece in the middle of a broken bridge
RAIL_THICKNESS = 0.2
RAIL_HEIGHT = 0.6
WALL_THICKNESS = 0.3
WALL_HEIGHT = 1.0
GOAL_SIZE = 2.0
GOAL_POST_SIZE = 0.4
GOAL_POST_HEIGHT = 1.5


def make_river(rng: random.Random) -> Rect:
    x0 = rng.uniform(9.0, 13.0)
    return Rect(x0, 0.0, x0 + RIVER_WIDTH, HEIGHT)


def make_bridge(river: Rect, y0: float, broken: bool) -> tuple[list[Patch], list[Box]]:
    """The deck patches and railing boxes of one bridge across ``river`` at ``y0``.

    A broken bridge is missing ``GAP_WIDTH`` of deck and railing in the middle of the
    river, so from the ramp the robot sees water between two pieces of deck.
    """
    y1 = y0 + BRIDGE_WIDTH
    deck_x0 = river.x0 - RAMP_LENGTH
    deck_x1 = river.x1 + RAMP_LENGTH
    rail_rows = (
        Rect(river.x0, y0 - RAIL_THICKNESS, river.x1, y0),
        Rect(river.x0, y1, river.x1, y1 + RAIL_THICKNESS),
    )
    if not broken:
        patches = [Patch(Rect(deck_x0, y0, deck_x1, y1), Terrain.BRIDGE)]
        boxes = [Box(rail, RAIL_HEIGHT, Colors.RAILING) for rail in rail_rows]
        return patches, boxes
    middle = river.center[0]
    gap_x0, gap_x1 = middle - GAP_WIDTH / 2, middle + GAP_WIDTH / 2
    patches = [
        Patch(Rect(deck_x0, y0, gap_x0, y1), Terrain.BRIDGE),
        Patch(Rect(gap_x1, y0, deck_x1, y1), Terrain.BRIDGE),
    ]
    boxes = [
        Box(Rect(rail.x0, rail.y0, gap_x0, rail.y1), RAIL_HEIGHT, Colors.RAILING)
        for rail in rail_rows
    ] + [
        Box(Rect(gap_x1, rail.y0, rail.x1, rail.y1), RAIL_HEIGHT, Colors.RAILING)
        for rail in rail_rows
    ]
    return patches, boxes


def make_goal(rng: random.Random, river: Rect) -> tuple[Patch, Box]:
    """The goal patch on the east bank and the tall post in its middle."""
    x0 = rng.uniform(river.x1 + 3.0, WIDTH - 2.0 - GOAL_SIZE)
    y0 = rng.uniform(2.0, HEIGHT - 2.0 - GOAL_SIZE)
    goal = Rect(x0, y0, x0 + GOAL_SIZE, y0 + GOAL_SIZE)
    cx, cy = goal.center
    half = GOAL_POST_SIZE / 2
    post = Box(
        Rect(cx - half, cy - half, cx + half, cy + half), GOAL_POST_HEIGHT, Colors.GOAL, solid=False
    )
    return Patch(goal, Terrain.GOAL), post


def make_start(rng: random.Random, river: Rect) -> Pose:
    """Somewhere on the west bank, facing a random direction."""
    return Pose(
        rng.uniform(2.0, river.x0 - 4.0), rng.uniform(2.0, HEIGHT - 2.0), rng.uniform(0, 360)
    )


def make_walls() -> list[Box]:
    rects = (
        Rect(0.0, 0.0, WIDTH, WALL_THICKNESS),
        Rect(0.0, HEIGHT - WALL_THICKNESS, WIDTH, HEIGHT),
        Rect(0.0, 0.0, WALL_THICKNESS, HEIGHT),
        Rect(WIDTH - WALL_THICKNESS, 0.0, WIDTH, HEIGHT),
    )
    return [Box(rect, WALL_HEIGHT, Colors.WALL) for rect in rects]
