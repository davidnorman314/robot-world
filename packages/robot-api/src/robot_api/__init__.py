"""The API a robot program uses to see and drive around in robot-world.

A robot program is a Python package that provides a ``run(robot)`` function and
registers it as an entry point in the ``robot_world.robots`` group::

    [project.entry-points."robot_world.robots"]
    my_robot = "my_robot:run"

The simulator calls ``run`` with a :class:`Robot`. The function drives the robot
using commands like :meth:`Robot.forward` and :meth:`Robot.turn`, and looks at the
world with :meth:`Robot.look`. The episode ends on its own when the robot reaches
the goal, drives into water, or runs out of time.
"""

from robot_api.colors import Color, Colors
from robot_api.image import Image
from robot_api.robot import EpisodeOver, Robot

__all__ = ["Color", "Colors", "EpisodeOver", "Image", "Robot"]
