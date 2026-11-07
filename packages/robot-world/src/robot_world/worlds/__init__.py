"""World generators. Each takes a seed and returns a :class:`robot_world.world.World`.

A generator's docstring is the description players see when they pick the world, so
write it for them: what the world looks like and what the robot has to do.
"""

import inspect
from collections.abc import Callable

from robot_world.world import World
from robot_world.worlds.river import make_river_world

WORLDS: dict[str, Callable[[int], World]] = {
    "river": make_river_world,
}


def world_description(name: str) -> str:
    """The player-facing description of a world, or "" if there is none."""
    generator = WORLDS.get(name)
    if generator is None:
        return ""
    return inspect.getdoc(generator) or ""
