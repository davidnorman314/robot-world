"""A picture taken by the robot's camera."""

import numpy as np

from robot_api.colors import Color


class Image:
    """A camera picture.

    Pixel ``(x, y)`` has ``x`` going from 0 on the left to ``width - 1`` on the right,
    and ``y`` going from 0 at the top to ``height - 1`` at the bottom.
    """

    def __init__(self, pixels: np.ndarray) -> None:
        if pixels.ndim != 3 or pixels.shape[2] != 3:
            raise ValueError(f"pixels must have shape (height, width, 3), got {pixels.shape}")
        self._pixels = np.ascontiguousarray(pixels, dtype=np.uint8)

    @property
    def pixels(self) -> np.ndarray:
        """The raw pixels as a numpy array of shape ``(height, width, 3)``.

        ``pixels[y, x]`` is the red, green and blue values of one pixel.
        """
        return self._pixels

    @property
    def width(self) -> int:
        """How many pixels wide the picture is."""
        return self._pixels.shape[1]

    @property
    def height(self) -> int:
        """How many pixels tall the picture is."""
        return self._pixels.shape[0]

    def pixel(self, x: int, y: int) -> Color:
        """The color of the pixel at column ``x`` and row ``y``."""
        r, g, b = self._pixels[y, x]
        return Color(int(r), int(g), int(b))

    def mask(self, color: Color) -> np.ndarray:
        """A boolean array of shape ``(height, width)`` that is True where ``color`` is."""
        return np.all(self._pixels == np.asarray(color, dtype=np.uint8), axis=2)

    def count(self, color: Color) -> int:
        """How many pixels have exactly this ``color``."""
        return int(self.mask(color).sum())

    def center(self, color: Color) -> tuple[float, float] | None:
        """The average ``(x, y)`` position of all pixels with this ``color``.

        Returns None if the color is nowhere in the picture. A center ``x`` less than
        ``width / 2`` means the color is mostly on the left side of the picture.
        """
        ys, xs = np.nonzero(self.mask(color))
        if len(xs) == 0:
            return None
        return float(xs.mean()), float(ys.mean())

    def __repr__(self) -> str:
        return f"Image({self.width}x{self.height})"
