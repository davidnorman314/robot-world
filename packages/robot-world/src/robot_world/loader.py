"""Loads a robot program from a wheel file.

A robot program is a pure-Python wheel that registers a ``run(robot)`` function as an
entry point in the ``robot_world.robots`` group. Pure-Python wheels are zip files that
Python can import from directly, so the wheel is added to ``sys.path`` rather than
installed.
"""

import sys
from importlib.metadata import distributions
from pathlib import Path

from robot_world.runner import Program

ENTRY_POINT_GROUP = "robot_world.robots"


class ProgramLoadError(Exception):
    """The wheel could not be loaded as a robot program. The message says why."""


def load_program(wheel: Path) -> Program:
    wheel = Path(wheel)
    if not wheel.is_file():
        raise ProgramLoadError(f"wheel not found: {wheel}")
    if wheel.suffix != ".whl":
        raise ProgramLoadError(f"expected a .whl file, got {wheel.name}")

    entry_points = [
        entry_point
        for distribution in distributions(path=[str(wheel)])
        for entry_point in distribution.entry_points
        if entry_point.group == ENTRY_POINT_GROUP
    ]
    if not entry_points:
        raise ProgramLoadError(
            f"{wheel.name} has no entry point in the {ENTRY_POINT_GROUP!r} group. "
            'Add [project.entry-points."robot_world.robots"] with name = "module:run" '
            "to pyproject.toml and rebuild the wheel."
        )
    if len(entry_points) > 1:
        names = ", ".join(entry_point.name for entry_point in entry_points)
        raise ProgramLoadError(
            f"{wheel.name} must have exactly one {ENTRY_POINT_GROUP!r} entry point, "
            f"found {len(entry_points)}: {names}"
        )

    if str(wheel) not in sys.path:
        sys.path.insert(0, str(wheel))
    entry_point = entry_points[0]
    try:
        program = entry_point.load()
    except Exception as exc:
        raise ProgramLoadError(
            f"could not load entry point {entry_point.value!r} from {wheel.name}: {exc}"
        ) from exc
    if not callable(program):
        raise ProgramLoadError(f"entry point {entry_point.value!r} is not a function")
    return program
