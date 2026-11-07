"""The robot a program drives around."""

from abc import ABC, abstractmethod

from robot_api.image import Image


class EpisodeOver(BaseException):  # noqa: N818 - not an error, a signal like SystemExit
    """Raised inside a robot program when the episode has ended.

    The episode ends when the robot reaches the goal, drives into water, or runs out
    of time. A robot program should not catch this.
    """

    def __init__(self, outcome: str) -> None:
        super().__init__(outcome)
        self.outcome = outcome


class Robot(ABC):
    """A tracked robot with a camera.

    Distances are in meters and angles are in degrees. The robot moves at a fixed
    speed, so a longer distance takes more simulated time.
    """

    @abstractmethod
    def forward(self, distance: float) -> float:
        """Drive straight ahead by ``distance`` meters.

        Stops early if something blocks the way. Returns how far the robot really
        moved.
        """

    @abstractmethod
    def backward(self, distance: float) -> float:
        """Drive straight backwards by ``distance`` meters.

        Stops early if something blocks the way. Returns how far the robot really
        moved.
        """

    @abstractmethod
    def turn(self, degrees: float) -> None:
        """Turn on the spot. Positive turns left, negative turns right."""

    @abstractmethod
    def look(self) -> Image:
        """Take a picture with the camera and return it."""

    @abstractmethod
    def heading(self) -> float:
        """The compass direction the robot faces, from 0 up to 360 degrees.

        0 is east, 90 is north, 180 is west and 270 is south.
        """

    @abstractmethod
    def say(self, message: str) -> None:
        """Print a message that is shown alongside the robot's view."""
