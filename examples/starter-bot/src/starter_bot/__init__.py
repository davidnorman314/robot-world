"""A starter robot. It drives in a big square and does not look where it is going."""

from robot_api import Robot


# robot-world calls this once. The run ends by itself when the robot reaches the goal,
# drives into water, or runs out of time.
def run(robot: Robot) -> None:
    robot.say("Hello! I am going to drive in a square.")
    for side in range(4):
        robot.say(f"Side {side + 1}")
        robot.forward(10.0)
        robot.turn(90)
    robot.say("Done. I never looked for the goal.")
