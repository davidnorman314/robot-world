"""one-bridge must be solvable: the test bot proves it on many seeds."""

import pytest

from robot_world.runner import run_program
from robot_world.sim import Outcome
from robot_world.worlds.one_bridge import make_one_bridge_world

from .bots import one_bridge_bot


@pytest.mark.parametrize("seed", range(20))
def test_one_bridge_bot_reaches_the_goal(seed):
    result = run_program(make_one_bridge_world(seed), one_bridge_bot.run)
    messages = [text for _, text in result.recording.messages]
    assert result.outcome is Outcome.SUCCESS, f"{result.outcome} after {messages}\n{result.error}"
    assert result.time < 120.0
