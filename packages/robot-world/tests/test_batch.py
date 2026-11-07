"""Running one program through many seeds, several episodes at a time."""

from robot_world.batch import run_batch
from robot_world.runner import run_program
from robot_world.sim import Outcome
from robot_world.world import Patch, Pose, Rect, Terrain, World


def make_world(seed: int) -> World:
    """The goal sits ``seed`` metres east of the robot, so each seed takes its own time."""
    return World(
        width=30.0,
        height=20.0,
        patches=(Patch(Rect(5.0 + seed, 4.0, 7.0 + seed, 6.0), Terrain.GOAL),),
        boxes=(),
        start=Pose(5.0, 5.0, 0.0),
        time_limit=30.0,
    )


def drive_east(robot) -> None:
    robot.say("off we go")
    robot.forward(20.0)


def run_episode(world: World):
    return run_program(world, drive_east)


def test_every_seed_is_run_against_its_own_world():
    results = dict(run_batch(make_world, run_episode, range(1, 5)))
    assert sorted(results) == [1, 2, 3, 4]
    for seed, result in results.items():
        assert result.outcome is Outcome.SUCCESS
        assert result.time == seed  # the goal patch starts `seed` metres east of the start


def test_results_come_back_as_each_episode_finishes_with_several_workers():
    results = dict(run_batch(make_world, run_episode, [3, 1, 2], workers=3))
    assert sorted(results) == [1, 2, 3]


def test_an_empty_seed_list_yields_nothing():
    assert list(run_batch(make_world, run_episode, [])) == []
