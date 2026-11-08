"""simple-goal must be solvable by the most basic robot: turn until you see red, drive."""

import pytest

from robot_world.runner import run_program
from robot_world.sim import Outcome
from robot_world.worlds.simple_goal import make_simple_goal_world

from .bots import simple_goal_bot


@pytest.mark.parametrize("seed", range(20))
def test_simple_goal_bot_reaches_the_goal(seed):
    result = run_program(make_simple_goal_world(seed), simple_goal_bot.run)
    messages = [text for _, text in result.recording.messages]
    assert result.outcome is Outcome.SUCCESS, f"{result.outcome} after {messages}\n{result.error}"
    assert result.time < 60.0
