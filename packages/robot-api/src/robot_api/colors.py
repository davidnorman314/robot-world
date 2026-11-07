"""The colors the robot's camera can see.

Everything in the world is painted in exactly one of these flat colors, so a robot
program can tell what it is looking at by comparing colors exactly.
"""

from typing import NamedTuple


class Color(NamedTuple):
    """A color as red, green and blue values from 0 to 255."""

    r: int
    g: int
    b: int


class Colors:
    """Every color that can appear in a camera image."""

    SKY = Color(135, 206, 235)
    LAND = Color(96, 160, 64)
    WATER = Color(40, 90, 200)
    BRIDGE = Color(150, 100, 50)
    RAILING = Color(235, 225, 200)
    GOAL = Color(230, 60, 60)
    WALL = Color(120, 120, 120)
    ROCK = Color(80, 70, 60)

    @classmethod
    def names(cls) -> list[str]:
        """The names of all the colors, for example ``["SKY", "LAND", ...]``."""
        return [name for name, value in vars(cls).items() if isinstance(value, Color)]
