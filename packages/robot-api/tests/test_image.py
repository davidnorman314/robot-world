import numpy as np
import pytest

from robot_api import Color, Colors, Image


def make_image() -> Image:
    pixels = np.zeros((4, 6, 3), dtype=np.uint8)
    pixels[:] = Colors.SKY
    pixels[2:, :] = Colors.LAND
    pixels[3, 1:4] = Colors.BRIDGE
    return Image(pixels)


def test_image_dimensions():
    image = make_image()
    assert image.width == 6
    assert image.height == 4


def test_pixel_returns_a_color():
    image = make_image()
    assert image.pixel(0, 0) == Colors.SKY
    assert image.pixel(2, 3) == Colors.BRIDGE


def test_mask_marks_matching_pixels():
    mask = make_image().mask(Colors.BRIDGE)
    assert mask.shape == (4, 6)
    assert mask.dtype == np.bool_
    assert mask.sum() == 3
    assert mask[3, 1] and mask[3, 3] and not mask[3, 0]


def test_count_counts_matching_pixels():
    image = make_image()
    assert image.count(Colors.BRIDGE) == 3
    assert image.count(Colors.SKY) == 12
    assert image.count(Colors.GOAL) == 0


def test_center_returns_mean_position_of_color():
    image = make_image()
    assert image.center(Colors.BRIDGE) == (2.0, 3.0)
    # 9 land pixels: all of row 2 plus x = 0, 4, 5 of row 3.
    assert image.center(Colors.LAND) == pytest.approx((24 / 9, 21 / 9))


def test_center_is_none_when_color_absent():
    assert make_image().center(Colors.GOAL) is None


def test_image_rejects_wrong_shape():
    with pytest.raises(ValueError):
        Image(np.zeros((4, 6), dtype=np.uint8))


def test_colors_are_distinct():
    values = [getattr(Colors, name) for name in Colors.names()]
    assert len(values) == len(set(values))
    assert all(isinstance(value, Color) for value in values)
