import numpy as np

from robot_api import Colors
from robot_world.camera import Camera
from robot_world.world import Box, Patch, Pose, Rect, Terrain, World


def flat_world(patches=(), boxes=()) -> World:
    return World(
        width=40.0,
        height=40.0,
        patches=tuple(patches),
        boxes=tuple(boxes),
        start=Pose(20.0, 20.0, 0.0),
        time_limit=60.0,
    )


def color_mask(image: np.ndarray, color) -> np.ndarray:
    return np.all(image == np.array(color, dtype=np.uint8), axis=2)


def test_image_has_requested_shape_and_dtype():
    camera = Camera(width=64, height=48)
    image = camera.render(flat_world(), Pose(20.0, 20.0, 0.0))
    assert image.shape == (48, 64, 3)
    assert image.dtype == np.uint8


def test_top_is_sky_and_bottom_is_land():
    camera = Camera(width=64, height=48)
    image = camera.render(flat_world(), Pose(20.0, 20.0, 0.0))
    assert tuple(image[0, 32]) == Colors.SKY
    assert tuple(image[47, 32]) == Colors.LAND


def test_rendering_is_deterministic():
    camera = Camera(width=64, height=48)
    world = flat_world()
    first = camera.render(world, Pose(20.0, 20.0, 37.0))
    second = camera.render(world, Pose(20.0, 20.0, 37.0))
    assert np.array_equal(first, second)


def test_patch_directly_ahead_appears_in_the_lower_middle():
    goal = Patch(Rect(22.0, 19.0, 24.0, 21.0), Terrain.GOAL)
    camera = Camera(width=64, height=48)
    image = camera.render(flat_world(patches=[goal]), Pose(20.0, 20.0, 0.0))
    ys, xs = np.nonzero(color_mask(image, Colors.GOAL))
    assert len(xs) > 0
    assert abs(xs.mean() - 31.5) < 1.0
    assert ys.mean() > 24


def test_patch_to_the_left_appears_on_the_left_whatever_the_heading():
    camera = Camera(width=64, height=48)
    for heading in (0.0, 90.0, 180.0, 270.0, 45.0):
        rad = np.radians(heading)
        ahead = np.array([np.cos(rad), np.sin(rad)])
        left = np.array([-np.sin(rad), np.cos(rad)])
        cx, cy = np.array([20.0, 20.0]) + 3.0 * ahead + 1.5 * left
        goal = Patch(Rect(cx - 0.5, cy - 0.5, cx + 0.5, cy + 0.5), Terrain.GOAL)
        image = camera.render(flat_world(patches=[goal]), Pose(20.0, 20.0, heading))
        ys, xs = np.nonzero(color_mask(image, Colors.GOAL))
        assert len(xs) > 0, f"goal not visible at heading {heading}"
        assert xs.mean() < 28, f"goal not on the left at heading {heading}"


def test_box_ahead_hides_the_ground_behind_it_and_pokes_above_the_horizon():
    wall = Box(Rect(23.0, 10.0, 23.5, 30.0), height=1.0, color=Colors.WALL)
    goal = Patch(Rect(25.0, 19.0, 27.0, 21.0), Terrain.GOAL)
    camera = Camera(width=64, height=48)
    world = flat_world(patches=[goal], boxes=[wall])
    image = camera.render(world, Pose(20.0, 20.0, 0.0))
    assert not color_mask(image, Colors.GOAL).any()
    ys, _ = np.nonzero(color_mask(image, Colors.WALL))
    assert ys.min() < camera.horizon_row < ys.max()


def test_nearer_box_hides_farther_box():
    near = Box(Rect(22.0, 19.5, 22.5, 20.5), height=1.0, color=Colors.ROCK)
    far = Box(Rect(24.0, 19.5, 24.5, 20.5), height=1.0, color=Colors.WALL)
    camera = Camera(width=64, height=48)
    image = camera.render(flat_world(boxes=[far, near]), Pose(20.0, 20.0, 0.0))
    assert tuple(image[camera.horizon_row, 32]) == Colors.ROCK


def test_box_behind_the_camera_is_not_drawn():
    behind = Box(Rect(17.0, 19.5, 17.5, 20.5), height=1.0, color=Colors.ROCK)
    camera = Camera(width=64, height=48)
    image = camera.render(flat_world(boxes=[behind]), Pose(20.0, 20.0, 0.0))
    assert not color_mask(image, Colors.ROCK).any()
