"""World generators. Each takes a seed and returns a :class:`robot_world.world.World`.

A generator's docstring is the description players see when they pick the world, so
write it for them: what the world looks like and what the robot has to do.

``WORLDS`` is in order from easiest to hardest; the first one is the default.
"""

import inspect
from collections.abc import Callable

from robot_world.world import World
from robot_world.worlds.one_bridge import make_one_bridge_world
from robot_world.worlds.simple_goal import make_simple_goal_world
from robot_world.worlds.three_bridges import make_three_bridges_world

WORLDS: dict[str, Callable[[int], World]] = {
    "simple-goal": make_simple_goal_world,
    "one-bridge": make_one_bridge_world,
    "three-bridges": make_three_bridges_world,
}
DEFAULT_WORLD = next(iter(WORLDS))


def world_description(name: str) -> str:
    """The player-facing description of a world, or "" if there is none."""
    generator = WORLDS.get(name)
    if generator is None:
        return ""
    return inspect.getdoc(generator) or ""
