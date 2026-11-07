import math

import pytest

from robot_api import Colors
from robot_world.sim import Outcome, Simulation
from robot_world.world import Box, Patch, Pose, Rect, Terrain, World

START = Pose(5.0, 5.0, 0.0)


def make_world(patches=(), boxes=(), start=START, time_limit=100.0) -> World:
    return World(
        width=20.0,
        height=20.0,
        patches=tuple(patches),
        boxes=tuple(boxes),
        start=start,
        time_limit=time_limit,
    )


def test_simulation_starts_at_the_world_start_pose():
    sim = Simulation(make_world())
    assert sim.pose == Pose(5.0, 5.0, 0.0)
    assert sim.time == 0.0
    assert sim.outcome is Outcome.RUNNING


def test_move_forward_travels_the_requested_distance_and_takes_time():
    sim = Simulation(make_world(), speed=2.0)
    moved = sim.move(3.0)
    assert moved == pytest.approx(3.0)
    assert sim.pose.x == pytest.approx(8.0)
    assert sim.pose.y == pytest.approx(5.0)
    assert sim.time == pytest.approx(1.5)


def test_move_follows_the_heading():
    sim = Simulation(make_world(start=Pose(5.0, 5.0, 90.0)))
    sim.move(2.0)
    assert sim.pose.x == pytest.approx(5.0)
    assert sim.pose.y == pytest.approx(7.0)


def test_negative_distance_moves_backwards():
    sim = Simulation(make_world())
    moved = sim.move(-2.0)
    assert moved == pytest.approx(-2.0)
    assert sim.pose.x == pytest.approx(3.0)


def test_turn_changes_heading_and_takes_time():
    sim = Simulation(make_world(), turn_speed=90.0)
    sim.turn(45.0)
    assert sim.pose.heading == pytest.approx(45.0)
    assert sim.time == pytest.approx(0.5)
    sim.turn(-90.0)
    assert sim.pose.heading == pytest.approx(315.0)
    assert sim.time == pytest.approx(1.5)


def test_move_stops_at_a_solid_box_and_reports_the_shorter_distance():
    rock = Box(Rect(8.0, 4.0, 9.0, 6.0), height=1.0, color=Colors.ROCK)
    sim = Simulation(make_world(boxes=[rock]), robot_radius=0.3)
    moved = sim.move(10.0)
    assert 2.5 < moved < 2.75
    assert sim.pose.x < 7.75
    assert sim.outcome is Outcome.RUNNING
    assert sim.bumped


def test_move_stops_at_the_edge_of_the_world():
    sim = Simulation(make_world(start=Pose(18.0, 5.0, 0.0)), robot_radius=0.3)
    moved = sim.move(5.0)
    assert moved < 2.0
    assert sim.pose.x <= 19.7


def test_driving_into_water_ends_the_episode():
    water = Patch(Rect(8.0, 0.0, 10.0, 20.0), Terrain.WATER)
    sim = Simulation(make_world(patches=[water]))
    moved = sim.move(10.0)
    assert sim.outcome is Outcome.DROWNED
    assert moved < 4.0
    assert sim.world.terrain_at(sim.pose.x, sim.pose.y) is Terrain.WATER


def test_reaching_the_goal_ends_the_episode_with_success():
    goal = Patch(Rect(8.0, 4.0, 10.0, 6.0), Terrain.GOAL)
    sim = Simulation(make_world(patches=[goal]))
    sim.move(10.0)
    assert sim.outcome is Outcome.SUCCESS
    assert 8.0 <= sim.pose.x < 10.0


def test_running_out_of_time_ends_the_episode():
    sim = Simulation(make_world(time_limit=2.0), speed=1.0)
    sim.move(1.0)
    assert sim.outcome is Outcome.RUNNING
    sim.turn(360.0)
    assert sim.outcome is Outcome.TIMEOUT
    assert sim.time == pytest.approx(2.0)


def test_commands_after_the_episode_is_over_do_nothing():
    sim = Simulation(make_world(time_limit=1.0))
    sim.move(5.0)
    assert sim.outcome is Outcome.TIMEOUT
    x = sim.pose.x
    assert sim.move(1.0) == 0.0
    assert sim.pose.x == x


def test_look_renders_the_camera_and_costs_a_little_time():
    sim = Simulation(make_world(), look_time=0.1)
    image = sim.look()
    assert image.shape == (sim.camera.height, sim.camera.width, 3)
    assert sim.time == pytest.approx(0.1)


def test_recording_captures_every_tick_and_every_look():
    sim = Simulation(make_world(), dt=0.1, speed=1.0)
    sim.move(1.0)
    sim.look()
    sim.say("hello")
    recording = sim.recording
    assert len(recording.frames) == 12  # the start pose, ten move ticks, one look tick
    assert recording.frames[0].time == 0.0
    assert recording.frames[-1].pose.x == pytest.approx(6.0)
    assert len(recording.looks) == 1
    assert recording.looks[0].frame == 11
    assert recording.messages == [(11, "hello")]


def test_on_tick_is_called_for_every_tick():
    ticks = []
    sim = Simulation(make_world(), dt=0.5, speed=1.0, on_tick=lambda s: ticks.append(s.time))
    sim.move(1.0)
    assert ticks == pytest.approx([0.5, 1.0])


def test_heading_stays_in_range():
    sim = Simulation(make_world(start=Pose(5.0, 5.0, 350.0)))
    sim.turn(20.0)
    assert 0.0 <= sim.pose.heading < 360.0
    assert math.isclose(sim.pose.heading, 10.0)
