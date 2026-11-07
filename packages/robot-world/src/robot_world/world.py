"""The static description of a world: terrain patches, obstacles and the start pose."""

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any

from robot_api import Color, Colors


class Terrain(StrEnum):
    """What the ground is made of at a point."""

    LAND = "land"
    WATER = "water"
    BRIDGE = "bridge"
    GOAL = "goal"


TERRAIN_COLORS: dict[Terrain, Color] = {
    Terrain.LAND: Colors.LAND,
    Terrain.WATER: Colors.WATER,
    Terrain.BRIDGE: Colors.BRIDGE,
    Terrain.GOAL: Colors.GOAL,
}


@dataclass(frozen=True)
class Rect:
    """An axis-aligned rectangle covering ``x0 <= x < x1`` and ``y0 <= y < y1``."""

    x0: float
    y0: float
    x1: float
    y1: float

    def __post_init__(self) -> None:
        if self.x1 <= self.x0 or self.y1 <= self.y0:
            raise ValueError(f"rect corners are inverted: {self}")

    def contains(self, x: float, y: float) -> bool:
        return self.x0 <= x < self.x1 and self.y0 <= y < self.y1

    @property
    def center(self) -> tuple[float, float]:
        return (self.x0 + self.x1) / 2, (self.y0 + self.y1) / 2

    @property
    def width(self) -> float:
        return self.x1 - self.x0

    @property
    def height(self) -> float:
        return self.y1 - self.y0

    def distance_squared_to(self, x: float, y: float) -> float:
        """Squared distance from a point to the nearest point of the rectangle."""
        dx = max(self.x0 - x, 0.0, x - self.x1)
        dy = max(self.y0 - y, 0.0, y - self.y1)
        return dx * dx + dy * dy


@dataclass(frozen=True)
class Patch:
    """A rectangle of ground painted with one terrain. Later patches paint over earlier ones."""

    rect: Rect
    terrain: Terrain


@dataclass(frozen=True)
class Box:
    """A box standing on the ground. Solid boxes block the robot; others are just visible."""

    rect: Rect
    height: float
    color: Color
    solid: bool = True


@dataclass(frozen=True)
class Pose:
    """Where the robot is and which way it faces. Heading is in degrees, 0 = east, 90 = north."""

    x: float
    y: float
    heading: float


@dataclass(frozen=True)
class World:
    """A complete world. Ground outside every patch is land."""

    width: float
    height: float
    patches: tuple[Patch, ...]
    boxes: tuple[Box, ...]
    start: Pose
    time_limit: float
    name: str = field(default="", compare=False)

    def terrain_at(self, x: float, y: float) -> Terrain:
        terrain = Terrain.LAND
        for patch in self.patches:
            if patch.rect.contains(x, y):
                terrain = patch.terrain
        return terrain

    @property
    def goal(self) -> Rect:
        """The goal patch. Raises if the world has none."""
        for patch in self.patches:
            if patch.terrain is Terrain.GOAL:
                return patch.rect
        raise LookupError("world has no goal patch")

    def is_blocked(self, x: float, y: float, radius: float) -> bool:
        """Whether a robot of the given radius centred here overlaps a wall or solid box."""
        if x - radius < 0 or x + radius > self.width or y - radius < 0 or y + radius > self.height:
            return True
        return any(
            box.solid and box.rect.distance_squared_to(x, y) < radius * radius for box in self.boxes
        )

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["patches"] = [
            {"rect": asdict(p.rect), "terrain": p.terrain.value} for p in self.patches
        ]
        data["boxes"] = [
            {"rect": asdict(b.rect), "height": b.height, "color": list(b.color), "solid": b.solid}
            for b in self.boxes
        ]
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "World":
        return cls(
            width=data["width"],
            height=data["height"],
            patches=tuple(Patch(Rect(**p["rect"]), Terrain(p["terrain"])) for p in data["patches"]),
            boxes=tuple(
                Box(Rect(**b["rect"]), b["height"], Color(*b["color"]), b["solid"])
                for b in data["boxes"]
            ),
            start=Pose(**data["start"]),
            time_limit=data["time_limit"],
            name=data.get("name", ""),
        )
