"""Adapts a :class:`Simulation` to the :class:`robot_api.Robot` interface."""

from robot_api import EpisodeOver, Image, Robot
from robot_world.sim import Simulation


class SimRobot(Robot):
    """The robot a program drives, backed directly by a simulation in this process.

    Every command raises :class:`EpisodeOver` once the episode has ended, so the
    program unwinds as soon as the robot reaches the goal, drowns or runs out of time.
    """

    def __init__(self, sim: Simulation) -> None:
        self.sim = sim

    def _check_over(self) -> None:
        if self.sim.outcome.is_over:
            raise EpisodeOver(self.sim.outcome.value)

    def forward(self, distance: float) -> float:
        self._check_over()
        moved = self.sim.move(float(distance))
        self._check_over()
        return moved

    def backward(self, distance: float) -> float:
        self._check_over()
        moved = -self.sim.move(-float(distance))
        self._check_over()
        return moved

    def turn(self, degrees: float) -> None:
        self._check_over()
        self.sim.turn(float(degrees))
        self._check_over()

    def look(self) -> Image:
        self._check_over()
        image = Image(self.sim.look())
        self._check_over()
        return image

    def heading(self) -> float:
        self._check_over()
        return self.sim.pose.heading

    def say(self, message: str) -> None:
        self._check_over()
        self.sim.say(str(message))
