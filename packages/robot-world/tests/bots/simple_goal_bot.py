"""Solves simple-goal: turn until the red goal is in view, then steer towards it."""

from robot_api import Colors, Robot

STEP = 0.5


def run(robot: Robot) -> None:
    robot.say("Looking for the goal")
    while True:
        image = robot.look()
        goal = image.center(Colors.GOAL)
        if goal is None:
            robot.turn(45)
            continue
        x, _ = goal
        off_center = (x - image.width / 2) / (image.width / 2)
        robot.turn(-off_center * 45)
        robot.forward(STEP)
