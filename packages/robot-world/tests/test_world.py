import pytest

from robot_api import Colors
from robot_world.world import Box, Patch, Pose, Rect, Terrain, World


def test_rect_contains_points_inside_but_not_outside():
    rect = Rect(1.0, 2.0, 3.0, 5.0)
    assert rect.contains(2.0, 3.0)
    assert rect.contains(1.0, 2.0)
    assert not rect.contains(3.0, 3.0)
    assert not rect.contains(0.5, 3.0)


def test_rect_rejects_inverted_corners():
    with pytest.raises(ValueError):
        Rect(3.0, 0.0, 1.0, 1.0)


def test_rect_center_and_size():
    rect = Rect(1.0, 2.0, 3.0, 6.0)
    assert rect.center == (2.0, 4.0)
    assert rect.width == 2.0
    assert rect.height == 4.0


def make_world(**overrides) -> World:
    fields = dict(
        width=10.0,
        height=8.0,
        patches=(
            Patch(Rect(4.0, 0.0, 6.0, 8.0), Terrain.WATER),
            Patch(Rect(4.0, 3.0, 6.0, 5.0), Terrain.BRIDGE),
            Patch(Rect(8.0, 6.0, 9.0, 7.0), Terrain.GOAL),
        ),
        boxes=(Box(Rect(1.0, 1.0, 2.0, 2.0), height=1.0, color=Colors.ROCK),),
        start=Pose(0.5, 0.5, 0.0),
        time_limit=60.0,
    )
    fields.update(overrides)
    return World(**fields)


def test_terrain_defaults_to_land():
    assert make_world().terrain_at(0.5, 0.5) is Terrain.LAND


def test_later_patches_paint_over_earlier_ones():
    world = make_world()
    assert world.terrain_at(5.0, 1.0) is Terrain.WATER
    assert world.terrain_at(5.0, 4.0) is Terrain.BRIDGE
    assert world.terrain_at(8.5, 6.5) is Terrain.GOAL


def test_outside_the_world_is_blocked():
    world = make_world()
    assert world.is_blocked(-0.1, 4.0, 0.0)
    assert world.is_blocked(10.1, 4.0, 0.0)
    assert world.is_blocked(5.0, -0.1, 0.0)
    assert not world.is_blocked(5.0, 4.0, 0.0)


def test_robot_circle_touching_a_solid_box_is_blocked():
    world = make_world()
    assert world.is_blocked(1.5, 1.5, 0.3)
    assert world.is_blocked(2.2, 1.5, 0.3)
    assert not world.is_blocked(2.4, 1.5, 0.3)
    assert not world.is_blocked(2.2, 2.2, 0.2)


def test_non_solid_boxes_do_not_block():
    world = make_world(
        boxes=(Box(Rect(1.0, 1.0, 2.0, 2.0), height=1.0, color=Colors.GOAL, solid=False),)
    )
    assert not world.is_blocked(1.5, 1.5, 0.3)


def test_world_round_trips_through_dict():
    world = make_world()
    assert World.from_dict(world.to_dict()) == world
