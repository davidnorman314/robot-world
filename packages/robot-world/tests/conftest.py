import textwrap
import zipfile
from pathlib import Path

import pytest

from robot_world.world import Patch, Pose, Rect, Terrain, World


def build_wheel(
    directory: Path,
    name: str,
    source: str,
    entry_points: str | None = None,
) -> Path:
    """Hand-build a minimal pure-Python wheel containing one module.

    ``entry_points`` is the text of ``entry_points.txt``; by default it registers
    ``name:run`` in the ``robot_world.robots`` group.
    """
    if entry_points is None:
        entry_points = f"[robot_world.robots]\n{name} = {name}:run\n"
    dist_info = f"{name}-0.1.0.dist-info"
    path = directory / f"{name}-0.1.0-py3-none-any.whl"
    with zipfile.ZipFile(path, "w") as whl:
        whl.writestr(f"{name}/__init__.py", textwrap.dedent(source))
        whl.writestr(
            f"{dist_info}/METADATA", f"Metadata-Version: 2.1\nName: {name}\nVersion: 0.1.0\n"
        )
        whl.writestr(
            f"{dist_info}/WHEEL", "Wheel-Version: 1.0\nRoot-Is-Purelib: true\nTag: py3-none-any\n"
        )
        whl.writestr(f"{dist_info}/entry_points.txt", entry_points)
        whl.writestr(f"{dist_info}/RECORD", "")
    return path


@pytest.fixture
def wheel_builder(tmp_path: Path):
    def build(name: str, source: str, entry_points: str | None = None) -> Path:
        return build_wheel(tmp_path, name, source, entry_points)

    return build


@pytest.fixture
def goal_ahead_world() -> World:
    """A 20x20 world with the robot at (5, 5) facing east and the goal at x = 8..10."""
    return World(
        width=20.0,
        height=20.0,
        patches=(Patch(Rect(8.0, 4.0, 10.0, 6.0), Terrain.GOAL),),
        boxes=(),
        start=Pose(5.0, 5.0, 0.0),
        time_limit=30.0,
    )
