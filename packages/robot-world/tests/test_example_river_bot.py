"""The example river-bot must actually solve the river world, since it is her template."""

import importlib.util
from pathlib import Path

import pytest

from robot_world.runner import run_program
from robot_world.sim import Outcome
from robot_world.worlds.one_bridge import make_one_bridge_world

EXAMPLE = Path(__file__).parents[3] / "examples" / "river-bot" / "src" / "river_bot" / "__init__.py"


@pytest.fixture(scope="module")
def river_bot():
    spec = importlib.util.spec_from_file_location("river_bot", EXAMPLE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("seed", range(20))
def test_river_bot_reaches_the_goal_in_one_bridge(river_bot, seed):
    result = run_program(make_one_bridge_world(seed), river_bot.run)
    messages = [text for _, text in result.recording.messages]
    assert result.outcome is Outcome.SUCCESS, f"{result.outcome} after {messages}\n{result.error}"
    assert result.time < 120.0
