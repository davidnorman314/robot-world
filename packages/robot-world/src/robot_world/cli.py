"""The ``robot-world`` command line."""

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from robot_world.loader import ProgramLoadError, load_program
from robot_world.remote import run_wheel
from robot_world.worlds import WORLDS


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="robot-world", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    run = commands.add_parser("run", help="run a robot program through one or more episodes")
    run.add_argument("wheel", type=Path, help="the robot program's .whl file")
    run.add_argument("--world", default="river", choices=sorted(WORLDS), help="which world")
    run.add_argument("--seed", type=int, default=1, help="seed of the first episode")
    run.add_argument("--episodes", type=int, default=1, help="how many seeds to run, in order")
    run.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="real seconds the program may go without sending a command",
    )

    check = commands.add_parser("check", help="check that a wheel is a valid robot program")
    check.add_argument("wheel", type=Path)

    commands.add_parser("worlds", help="list the available worlds")
    return parser


def run_command(args: argparse.Namespace) -> int:
    if not args.wheel.is_file():
        print(f"wheel not found: {args.wheel}")
        return 1
    successes = 0
    for seed in range(args.seed, args.seed + args.episodes):
        world = WORLDS[args.world](seed)
        result = run_wheel(world, args.wheel, wall_timeout=args.timeout)
        print(f"{args.world} seed {seed}: {result.outcome.value} in {result.time:.1f} s")
        if result.error:
            print(result.error.rstrip())
        successes += result.succeeded
    if args.episodes > 1:
        print(f"{successes} of {args.episodes} succeeded")
    return 0 if successes == args.episodes else 1


def check_command(args: argparse.Namespace) -> int:
    try:
        program = load_program(args.wheel)
    except ProgramLoadError as exc:
        print(f"{args.wheel.name}: {exc}")
        return 1
    print(f"{args.wheel.name}: OK, runs {program.__module__}:{program.__name__}")
    return 0


def worlds_command(args: argparse.Namespace) -> int:
    for name in sorted(WORLDS):
        print(name)
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    handlers = {"run": run_command, "check": check_command, "worlds": worlds_command}
    return handlers[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
