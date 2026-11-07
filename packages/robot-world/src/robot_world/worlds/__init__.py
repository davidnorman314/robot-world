"""World generators. Each takes a seed and returns a :class:`robot_world.world.World`."""

from collections.abc import Callable

from robot_world.world import World
from robot_world.worlds.river import make_river_world

WORLDS: dict[str, Callable[[int], World]] = {
    "river": make_river_world,
}
