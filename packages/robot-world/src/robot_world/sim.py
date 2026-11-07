"""The simulation: moves the robot through a world tick by tick and records what happens."""

import math
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import StrEnum

import numpy as np

from robot_world.camera import Camera
from robot_world.world import Pose, Terrain, World


class Outcome(StrEnum):
    RUNNING = "running"
    SUCCESS = "success"  # the robot reached the goal
    DROWNED = "drowned"  # the robot drove into water
    TIMEOUT = "timeout"  # simulated time ran out
    FINISHED = "finished"  # the program returned without reaching the goal
    ERROR = "error"  # the program raised an exception
    STUCK = "stuck"  # the program stopped responding (wall-clock timeout)

    @property
    def is_over(self) -> bool:
        return self is not Outcome.RUNNING


@dataclass(frozen=True)
class Frame:
    time: float
    pose: Pose


@dataclass(frozen=True)
class Look:
    frame: int
    image: np.ndarray


@dataclass
class Recording:
    frames: list[Frame] = field(default_factory=list)
    looks: list[Look] = field(default_factory=list)
    messages: list[tuple[int, str]] = field(default_factory=list)


class Simulation:
    """Drives a robot through a world.

    Each command (``move``, ``turn``, ``look``) advances simulated time in ticks of
    ``dt`` seconds, records a frame per tick, and ends the episode when the robot
    reaches the goal, enters water, or runs out of time.
    """

    def __init__(
        self,
        world: World,
        *,
        camera: Camera | None = None,
        speed: float = 1.0,
        turn_speed: float = 90.0,
        dt: float = 0.05,
        robot_radius: float = 0.3,
        look_time: float = 0.1,
        on_tick: Callable[["Simulation"], None] | None = None,
    ) -> None:
        self.world = world
        self.camera = camera or Camera()
        self.speed = speed
        self.turn_speed = turn_speed
        self.dt = dt
        self.robot_radius = robot_radius
        self.look_time = look_time
        self.on_tick = on_tick
        self.pose = world.start
        self.time = 0.0
        self.outcome = Outcome.RUNNING
        self.bumped = False
        self.recording = Recording(frames=[Frame(0.0, world.start)])

    @property
    def frame_index(self) -> int:
        return len(self.recording.frames) - 1

    def move(self, distance: float) -> float:
        """Drive straight by ``distance`` meters (negative is backwards).

        Stops early at walls and solid boxes, or when the episode ends. Returns the
        signed distance actually travelled.
        """
        self.bumped = False
        direction = 1.0 if distance >= 0 else -1.0
        total = abs(distance)
        moved = 0.0
        ticks = 0
        start = self.pose
        heading = math.radians(start.heading)
        # Each tick's position is computed from the start pose and the tick count
        # rather than accumulated, so rounding errors do not build up over a long move.
        while total - moved > 1e-9 and not self.outcome.is_over:
            ticks += 1
            next_moved = min(total, ticks * self.speed * self.dt)
            x = start.x + direction * next_moved * math.cos(heading)
            y = start.y + direction * next_moved * math.sin(heading)
            if self.world.is_blocked(x, y, self.robot_radius):
                self.bumped = True
                break
            self.pose = Pose(x, y, start.heading)
            self._advance((next_moved - moved) / self.speed)
            moved = next_moved
        return direction * moved

    def turn(self, degrees: float) -> None:
        """Turn on the spot. Positive is left (counter-clockwise)."""
        direction = 1.0 if degrees >= 0 else -1.0
        total = abs(degrees)
        turned = 0.0
        ticks = 0
        start = self.pose
        while total - turned > 1e-9 and not self.outcome.is_over:
            ticks += 1
            next_turned = min(total, ticks * self.turn_speed * self.dt)
            heading = (start.heading + direction * next_turned) % 360.0
            self.pose = Pose(start.x, start.y, heading)
            self._advance((next_turned - turned) / self.turn_speed)
            turned = next_turned

    def look(self) -> np.ndarray:
        """Render the camera view, which takes ``look_time`` seconds."""
        image = self.camera.render(self.world, self.pose)
        if not self.outcome.is_over:
            self._advance(self.look_time)
        self.recording.looks.append(Look(self.frame_index, image))
        return image

    def say(self, message: str) -> None:
        self.recording.messages.append((self.frame_index, message))

    def end(self, outcome: Outcome) -> None:
        """End the episode for a reason outside the world, such as the program finishing."""
        if not self.outcome.is_over:
            self.outcome = outcome

    def _advance(self, seconds: float) -> None:
        self.time += seconds
        self.recording.frames.append(Frame(self.time, self.pose))
        terrain = self.world.terrain_at(self.pose.x, self.pose.y)
        if terrain is Terrain.WATER:
            self.outcome = Outcome.DROWNED
        elif terrain is Terrain.GOAL:
            self.outcome = Outcome.SUCCESS
        elif self.time >= self.world.time_limit - 1e-9:
            self.outcome = Outcome.TIMEOUT
        if self.on_tick is not None:
            self.on_tick(self)
