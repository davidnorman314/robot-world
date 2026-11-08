"""The starter template must run cleanly, and must not solve anything: it is her blank page."""

import importlib.util
from pathlib import Path

import pytest

from robot_world.runner import run_program
from robot_world.sim import Outcome
from robot_world.worlds.one_bridge import make_one_bridge_world
from robot_world.worlds.simple_goal import make_simple_goal_world

EXAMPLES = Path(__file__).parents[3] / "examples"
EXAMPLE = EXAMPLES / "starter-bot" / "src" / "starter_bot" / "__init__.py"


@pytest.fixture(scope="module")
def starter_bot():
    spec = importlib.util.spec_from_file_location("starter_bot", EXAMPLE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_starter_bot_runs_to_the_end_without_errors(starter_bot):
    result = run_program(make_simple_goal_world(1), starter_bot.run)
    assert result.error is None
    assert result.outcome is not Outcome.ERROR
    assert result.recording.messages, "the starter should show how robot.say works"


def test_starter_bot_often_drowns_in_one_bridge(starter_bot):
    outcomes = [
        run_program(make_one_bridge_world(seed), starter_bot.run).outcome for seed in range(20)
    ]
    assert Outcome.SUCCESS not in outcomes
    assert outcomes.count(Outcome.DROWNED) >= 5, outcomes
