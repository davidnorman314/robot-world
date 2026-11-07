"""three-bridges must be solvable: the test bot proves it on many seeds."""

import pytest

from robot_world.runner import run_program
from robot_world.sim import Outcome
from robot_world.worlds.three_bridges import make_three_bridges_world

from .bots import three_bridges_bot


@pytest.mark.parametrize("seed", range(20))
def test_three_bridges_bot_reaches_the_goal(seed):
    result = run_program(make_three_bridges_world(seed), three_bridges_bot.run)
    messages = [text for _, text in result.recording.messages]
    assert result.outcome is Outcome.SUCCESS, f"{result.outcome} after {messages}\n{result.error}"
    assert result.time < 300.0
