import pytest

from robot_api import EpisodeOver, Image, Robot
from robot_world.sim import Outcome, Simulation
from robot_world.sim_robot import SimRobot


@pytest.fixture
def robot(goal_ahead_world):
    return SimRobot(Simulation(goal_ahead_world))


def test_sim_robot_is_a_robot(robot):
    assert isinstance(robot, Robot)


def test_forward_and_backward_return_distance_moved(robot):
    assert robot.forward(1.0) == pytest.approx(1.0)
    assert robot.backward(0.5) == pytest.approx(0.5)
    assert robot.sim.pose.x == pytest.approx(5.5)


def test_turn_and_heading(robot):
    assert robot.heading() == 0.0
    robot.turn(90.0)
    assert robot.heading() == pytest.approx(90.0)
    robot.turn(-180.0)
    assert robot.heading() == pytest.approx(270.0)


def test_look_returns_an_image(robot):
    image = robot.look()
    assert isinstance(image, Image)
    assert (image.width, image.height) == (robot.sim.camera.width, robot.sim.camera.height)


def test_say_is_recorded(robot):
    robot.say("hi")
    assert robot.sim.recording.messages == [(0, "hi")]


def test_reaching_the_goal_raises_episode_over(robot):
    with pytest.raises(EpisodeOver) as info:
        robot.forward(10.0)
    assert info.value.outcome == Outcome.SUCCESS
    assert robot.sim.outcome is Outcome.SUCCESS


def test_every_command_raises_once_the_episode_is_over(robot):
    with pytest.raises(EpisodeOver):
        robot.forward(10.0)
    for command in (lambda: robot.forward(1), lambda: robot.turn(1), robot.look, robot.heading):
        with pytest.raises(EpisodeOver):
            command()
