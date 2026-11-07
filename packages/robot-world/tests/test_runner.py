import pytest

from robot_api import EpisodeOver, Robot
from robot_world.runner import EpisodeResult, run_program
from robot_world.sim import Outcome


def test_program_that_reaches_the_goal_succeeds(goal_ahead_world):
    def program(robot: Robot) -> None:
        robot.forward(10.0)

    result = run_program(goal_ahead_world, program)
    assert isinstance(result, EpisodeResult)
    assert result.outcome is Outcome.SUCCESS
    assert result.time == pytest.approx(3.0)
    assert result.error is None
    assert len(result.recording.frames) > 1


def test_program_that_returns_early_is_finished(goal_ahead_world):
    def program(robot: Robot) -> None:
        robot.forward(1.0)

    result = run_program(goal_ahead_world, program)
    assert result.outcome is Outcome.FINISHED
    assert result.time == pytest.approx(1.0)


def test_program_that_raises_is_an_error_with_traceback(goal_ahead_world):
    def program(robot: Robot) -> None:
        robot.forward(1.0)
        raise ValueError("oops")

    result = run_program(goal_ahead_world, program)
    assert result.outcome is Outcome.ERROR
    assert "ValueError: oops" in result.error
    assert "program" in result.error


def test_swallowing_episode_over_does_not_change_the_outcome(goal_ahead_world):
    def program(robot: Robot) -> None:
        try:  # noqa: SIM105 - written the way a robot program would write it
            robot.forward(10.0)
        except EpisodeOver:
            pass

    result = run_program(goal_ahead_world, program)
    assert result.outcome is Outcome.SUCCESS


def test_run_program_passes_simulation_options(goal_ahead_world):
    ticks = []

    def program(robot: Robot) -> None:
        robot.forward(1.0)

    run_program(goal_ahead_world, program, dt=0.5, on_tick=lambda sim: ticks.append(sim.time))
    assert ticks == pytest.approx([0.5, 1.0])
