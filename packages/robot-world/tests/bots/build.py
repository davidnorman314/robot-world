"""Build the test bots into wheels, for demos in the viewer.

Each ``*_bot.py`` module here becomes its own wheel, in a folder named after the world it
solves, so ``robot-world serve <folder>`` picks it up::

    uv run python packages/robot-world/tests/bots/build.py            # into dist/bots/
    uv run python packages/robot-world/tests/bots/build.py some/dir

    uv run robot-world serve dist/bots/one-bridge --world one-bridge

The wheels are build products, not sources: they are ignored by git and rebuilt on demand.
"""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

BOTS = Path(__file__).parent
ROOT = BOTS.parents[3]
DEFAULT_OUT = ROOT / "dist" / "bots"

PYPROJECT = """\
[project]
name = "{module}"
version = "0.1.0"
description = "robot-world's test robot for the {world} world, built for demos"
requires-python = ">=3.12"
dependencies = ["robot-api"]

[project.entry-points."robot_world.robots"]
{world} = "{module}:run"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/{module}"]
"""


def bot_modules() -> list[Path]:
    """The bot modules in this folder, in name order."""
    return sorted(BOTS.glob("*_bot.py"))


def world_name(module: Path) -> str:
    """``one_bridge_bot.py`` solves the ``one-bridge`` world."""
    return module.stem.removesuffix("_bot").replace("_", "-")


def build_demo_bots(out_dir: Path = DEFAULT_OUT) -> list[Path]:
    """Build every bot into ``out_dir/<world>/<module>-0.1.0-py3-none-any.whl``.

    Returns the wheel paths. Each wheel's folder is emptied first, so it holds exactly
    one wheel and the viewer has no older one to pick instead.
    """
    wheels = []
    for module in bot_modules():
        world = world_name(module)
        dest = out_dir / world
        if dest.exists():
            shutil.rmtree(dest)
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / module.stem
            package = project / "src" / module.stem
            package.mkdir(parents=True)
            shutil.copy(module, package / "__init__.py")
            (project / "pyproject.toml").write_text(
                PYPROJECT.format(module=module.stem, world=world), encoding="utf-8"
            )
            subprocess.run(
                ["uv", "build", "--wheel", "--out-dir", str(dest), str(project)],
                check=True,
                capture_output=True,
            )
        (wheel,) = dest.glob("*.whl")
        wheels.append(wheel)
    return wheels


def main(argv: list[str]) -> None:
    out_dir = Path(argv[1]) if len(argv) > 1 else DEFAULT_OUT
    for wheel in build_demo_bots(out_dir):
        print(wheel.relative_to(Path.cwd()) if wheel.is_relative_to(Path.cwd()) else wheel)


if __name__ == "__main__":
    main(sys.argv)
