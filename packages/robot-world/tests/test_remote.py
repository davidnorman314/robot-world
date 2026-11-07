import time

import pytest

from robot_world.remote import run_wheel
from robot_world.sim import Outcome

pytestmark = pytest.mark.slow  # each test spawns a Python subprocess


def test_wheel_that_reaches_the_goal_succeeds(wheel_builder, goal_ahead_world):
    wheel = wheel_builder("goal_bot", "def run(robot):\n    robot.forward(10.0)\n")
    result = run_wheel(goal_ahead_world, wheel)
    assert result.outcome is Outcome.SUCCESS
    assert result.time == pytest.approx(3.0)
    assert result.error is None
    assert len(result.recording.frames) == 61


def test_wheel_that_returns_early_is_finished(wheel_builder, goal_ahead_world):
    wheel = wheel_builder("early_bot", "def run(robot):\n    robot.forward(1.0)\n")
    result = run_wheel(goal_ahead_world, wheel)
    assert result.outcome is Outcome.FINISHED
    assert result.time == pytest.approx(1.0)


def test_wheel_that_raises_is_an_error_with_traceback(wheel_builder, goal_ahead_world):
    source = """
        def run(robot):
            robot.turn(10)
            raise ValueError("oops")
    """
    result = run_wheel(goal_ahead_world, wheel_builder("bad_bot", source))
    assert result.outcome is Outcome.ERROR
    assert "ValueError: oops" in result.error
    assert "bad_bot" in result.error


def test_wheel_that_hangs_is_stuck_after_the_wall_timeout(wheel_builder, goal_ahead_world):
    source = """
        import time

        def run(robot):
            robot.forward(1.0)
            time.sleep(60)
    """
    started = time.monotonic()
    result = run_wheel(goal_ahead_world, wheel_builder("sleepy_bot", source), wall_timeout=0.5)
    assert time.monotonic() - started < 15
    assert result.outcome is Outcome.STUCK
    assert result.time == pytest.approx(1.0)
    assert "0.5" in result.error


def test_images_and_messages_cross_the_process_boundary(wheel_builder, goal_ahead_world):
    source = """
        from robot_api import Colors

        def run(robot):
            image = robot.look()
            robot.say(f"{image.width}x{image.height} sky={image.count(Colors.SKY) > 0}")
            robot.say(f"heading={robot.heading()}")
    """
    result = run_wheel(goal_ahead_world, wheel_builder("look_bot", source))
    assert result.outcome is Outcome.FINISHED
    assert [text for _, text in result.recording.messages] == ["128x96 sky=True", "heading=0.0"]
    assert len(result.recording.looks) == 1


def test_wheel_that_cannot_be_loaded_is_an_error(wheel_builder, goal_ahead_world):
    wheel = wheel_builder("no_entry", "def run(robot):\n    pass\n", entry_points="")
    result = run_wheel(goal_ahead_world, wheel)
    assert result.outcome is Outcome.ERROR
    assert "robot_world.robots" in result.error
    assert result.time == 0.0


def test_program_that_ignores_episode_over_is_still_a_success(wheel_builder, goal_ahead_world):
    source = """
        def run(robot):
            while True:
                try:
                    robot.forward(10.0)
                except BaseException:
                    pass
    """
    result = run_wheel(goal_ahead_world, wheel_builder("stubborn_bot", source), wall_timeout=0.5)
    assert result.outcome is Outcome.SUCCESS
