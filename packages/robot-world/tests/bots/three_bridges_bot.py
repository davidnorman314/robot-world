"""Solves three-bridges by walking the bank from the south end and checking each bridge.

1. Drive east to the river and back off a little.
2. Drive south along the bank until the fence.
3. Drive north. At each bridge ramp, line up with the middle of the deck, face east,
   and look along it: water right after the near deck means the bridge is broken.
4. Cross the first whole bridge, then find the red goal and drive to it.
"""

from robot_api import Color, Colors, Image, Robot

EAST = 0.0
NORTH = 90.0
SOUTH = 270.0
STEP = 0.5


def run(robot: Robot) -> None:
    robot.say("Driving east to the river")
    face(robot, EAST)
    drive_until_ground_ahead_is(robot, Colors.WATER, Colors.BRIDGE, Colors.RAILING)
    if ground_ahead(robot) == Colors.BRIDGE:
        robot.forward(1.2)  # onto the ramp, well clear of the railings
    else:
        robot.backward(1.0)  # off the water's edge, but still on the ramps' line

    robot.say("Driving south to the fence")
    face(robot, SOUTH)
    while robot.forward(STEP) == STEP:
        pass

    face(robot, NORTH)
    for attempt in range(1, 4):
        robot.say(f"Looking for bridge {attempt}")
        if not drive_until_ground_ahead_is(robot, Colors.BRIDGE):
            break
        robot.forward(1.0)
        line_up_with_the_deck(robot)
        face(robot, EAST)
        if bridge_ahead_is_broken(robot.look()):
            robot.say("This bridge is broken")
            face(robot, NORTH)
            drive_until_ground_ahead_is(robot, Colors.LAND)
            robot.forward(1.0)
            continue
        robot.say("Crossing the bridge")
        drive_until_ground_ahead_is(robot, Colors.LAND)
        robot.forward(1.0)
        robot.say("Looking for the goal")
        drive_to(robot, Colors.GOAL)
        return
    robot.say("No whole bridge found")


def bridge_ahead_is_broken(image: Image) -> bool:
    """Scan up the middle column: deck, then water means a gap, anything else is fine."""
    x = image.width // 2
    y = image.height - 1
    while y >= 0 and image.pixel(x, y) == Colors.BRIDGE:
        y -= 1
    return y >= 0 and image.pixel(x, y) == Colors.WATER


def line_up_with_the_deck(robot: Robot) -> None:
    face(robot, NORTH)
    drive_until_ground_ahead_is(robot, Colors.LAND)
    robot.backward(1.5)


def face(robot: Robot, heading: float) -> None:
    change = (heading - robot.heading() + 180) % 360 - 180
    robot.turn(change)


def ground_ahead(robot: Robot) -> Color:
    image = robot.look()
    return image.pixel(image.width // 2, image.height - 1)


def drive_until_ground_ahead_is(robot: Robot, *colors: Color) -> bool:
    """Drive in steps until the ground ahead is one of the colors. False if blocked."""
    while ground_ahead(robot) not in colors:
        if robot.forward(STEP) < STEP:
            robot.say("Bumped into something")
            return False
    return True


def drive_to(robot: Robot, color: Color) -> None:
    while True:
        image = robot.look()
        center = image.center(color)
        if center is None:
            robot.turn(45)
            continue
        x, _ = center
        off_center = (x - image.width / 2) / (image.width / 2)
        robot.turn(-off_center * 45)
        robot.forward(STEP)
