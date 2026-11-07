"""A flat-shaded ray-casting camera that renders what the robot sees.

Every pixel is painted the exact semantic color of whatever its ray hits first: a
box, the ground (whose color comes from the terrain patches) or the sky. There is no
lighting, so a robot program can identify things by comparing colors exactly.
"""

import math

import numpy as np

from robot_api import Colors
from robot_world.world import TERRAIN_COLORS, Pose, World


class Camera:
    def __init__(
        self,
        width: int = 128,
        height: int = 96,
        fov: float = 90.0,
        eye_height: float = 0.6,
        pitch: float = -10.0,
    ) -> None:
        self.width = width
        self.height = height
        self.fov = fov
        self.eye_height = eye_height
        self.pitch = pitch
        self._directions = self._camera_space_directions()

    def _camera_space_directions(self) -> np.ndarray:
        """Unit-free ray directions as (forward, left, up) for every pixel, pitch applied."""
        half_tan = math.tan(math.radians(self.fov) / 2)
        xs = (2 * (np.arange(self.width) + 0.5) / self.width - 1) * half_tan
        ys = (
            (1 - 2 * (np.arange(self.height) + 0.5) / self.height)
            * half_tan
            * (self.height / self.width)
        )
        u, v = np.meshgrid(xs, ys)
        forward = np.ones_like(u)
        left = -u
        up = v
        pitch = math.radians(self.pitch)
        forward_p = forward * math.cos(pitch) - up * math.sin(pitch)
        up_p = forward * math.sin(pitch) + up * math.cos(pitch)
        return np.stack([forward_p, left, up_p], axis=-1).reshape(-1, 3)

    @property
    def horizon_row(self) -> int:
        """The pixel row at which a ray is exactly horizontal."""
        half_tan = math.tan(math.radians(self.fov) / 2) * self.height / self.width
        v = -math.tan(math.radians(self.pitch))
        row = (1 - v / half_tan) * self.height / 2 - 0.5
        return int(round(row))

    def render(self, world: World, pose: Pose) -> np.ndarray:
        """Render the view from ``pose`` as an array of shape ``(height, width, 3)``."""
        heading = math.radians(pose.heading)
        cos_h, sin_h = math.cos(heading), math.sin(heading)
        forward, left, up = self._directions.T
        dx = forward * cos_h - left * sin_h
        dy = forward * sin_h + left * cos_h
        dz = up
        origin = np.array([pose.x, pose.y, self.eye_height])

        with np.errstate(divide="ignore", invalid="ignore"):
            t_ground = np.where(dz < 0, -origin[2] / dz, np.inf)

        pixels = np.empty((len(dx), 3), dtype=np.uint8)
        pixels[:] = Colors.SKY

        hits_ground = np.isfinite(t_ground)
        gx = origin[0] + t_ground[hits_ground] * dx[hits_ground]
        gy = origin[1] + t_ground[hits_ground] * dy[hits_ground]
        pixels[hits_ground] = self._ground_colors(world, gx, gy)

        nearest = t_ground
        directions = np.stack([dx, dy, dz], axis=-1)
        for box in world.boxes:
            t_box = self._box_distance(box, origin, directions)
            closer = t_box < nearest
            pixels[closer] = box.color
            nearest = np.where(closer, t_box, nearest)

        return pixels.reshape(self.height, self.width, 3)

    @staticmethod
    def _ground_colors(world: World, gx: np.ndarray, gy: np.ndarray) -> np.ndarray:
        colors = np.empty((len(gx), 3), dtype=np.uint8)
        colors[:] = Colors.LAND
        for patch in world.patches:
            r = patch.rect
            inside = (gx >= r.x0) & (gx < r.x1) & (gy >= r.y0) & (gy < r.y1)
            colors[inside] = TERRAIN_COLORS[patch.terrain]
        return colors

    @staticmethod
    def _box_distance(box, origin: np.ndarray, directions: np.ndarray) -> np.ndarray:
        """Distance along each ray to the box, or inf where the ray misses it."""
        low = np.array([box.rect.x0, box.rect.y0, 0.0])
        high = np.array([box.rect.x1, box.rect.y1, box.height])
        with np.errstate(divide="ignore", invalid="ignore"):
            inv = 1.0 / directions
            t_low = (low - origin) * inv
            t_high = (high - origin) * inv
        t_near = np.nanmax(np.minimum(t_low, t_high), axis=1)
        t_far = np.nanmin(np.maximum(t_low, t_high), axis=1)
        hit = (t_far >= t_near) & (t_near > 0)
        return np.where(hit, t_near, np.inf)
