"""A robot that crosses the river by the bridge and drives to the red goal.

The plan:

1. Face east and drive until the water (or the bridge) is right in front of us.
2. If it is water, back up a little, look north and south to see which way the bridge
   is, and drive along the bank until the bridge ramp is in front of us.
3. Drive onto the ramp and line up with the middle of it, so we miss the railings.
4. Face east and drive across the bridge until we are back on land.
5. Spin until we see the red goal, then keep steering towards it.

The robot's camera only sees flat colors, so we tell what is what by checking
``Colors`` exactly. The pixel at the bottom middle of a picture is the ground about
half a meter in front of the robot.
"""

from robot_api import Color, Colors, Image, Robot

EAST = 0.0
NORTH = 90.0
SOUTH = 270.0

STEP = 0.5  # how far to drive between looks, in meters


def run(robot: Robot) -> None:
    robot.say("Driving east to the river")
    face(robot, EAST)
    drive_until_ground_ahead_is(robot, Colors.WATER, Colors.BRIDGE, Colors.RAILING)

    if ground_ahead(robot) != Colors.BRIDGE:
        robot.say("Looking for the bridge")
        robot.backward(1.0)  # stay well away from the edge of the water
        face(robot, direction_of_bridge(robot))
        robot.say("Driving along the bank to the bridge")
        drive_until_ground_ahead_is(robot, Colors.BRIDGE)

    robot.say("Lining up with the middle of the bridge")
    robot.forward(1.0)  # onto the ramp
    face(robot, NORTH)
    drive_until_ground_ahead_is(robot, Colors.LAND)  # to the north edge of the ramp
    robot.backward(1.5)  # the ramp is 3 m wide, so this is the middle

    robot.say("Crossing the bridge")
    face(robot, EAST)
    drive_until_ground_ahead_is(robot, Colors.LAND)
    robot.forward(1.0)

    robot.say("Looking for the goal")
    drive_to(robot, Colors.GOAL)


def face(robot: Robot, heading: float) -> None:
    """Turn to point in the given compass direction, the short way round."""
    change = (heading - robot.heading() + 180) % 360 - 180
    robot.turn(change)


def ground_ahead(robot: Robot, image: Image | None = None) -> Color:
    """The color of the ground just in front of the robot."""
    if image is None:
        image = robot.look()
    return image.pixel(image.width // 2, image.height - 1)


def drive_until_ground_ahead_is(robot: Robot, *colors: Color) -> None:
    """Drive forward in small steps until the ground ahead has one of the colors."""
    while ground_ahead(robot) not in colors:
        moved = robot.forward(STEP)
        if moved < STEP:
            robot.say("Bumped into something")
            return


def direction_of_bridge(robot: Robot) -> float:
    """Look north and south along the river; the bridge is where we see more of it."""
    face(robot, NORTH)
    north = bridge_pixels(robot.look())
    face(robot, SOUTH)
    south = bridge_pixels(robot.look())
    return NORTH if north > south else SOUTH


def bridge_pixels(image: Image) -> int:
    """How much bridge is in the picture: the deck and the railings."""
    return image.count(Colors.BRIDGE) + image.count(Colors.RAILING)


def drive_to(robot: Robot, color: Color) -> None:
    """Spin until we see the color, then keep steering towards it and driving."""
    while True:
        image = robot.look()
        center = image.center(color)
        if center is None:
            robot.turn(45)
            continue
        x, _ = center
        # x is 0 at the left edge and image.width at the right edge. The camera sees
        # 90 degrees, so the left edge is 45 degrees left of straight ahead.
        off_center = (x - image.width / 2) / (image.width / 2)
        robot.turn(-off_center * 45)
        robot.forward(STEP)
