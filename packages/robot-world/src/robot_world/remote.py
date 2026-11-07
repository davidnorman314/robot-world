"""Runs a robot program from a wheel in a separate process.

The program's process holds a :class:`RemoteRobot`, a stand-in that forwards every
command over a pipe. The simulation itself stays in this process, so a program that
crashes, hangs or misbehaves can be stopped without taking the simulator down, and a
fresh wheel can be loaded for every episode.
"""

import contextlib
import multiprocessing
import traceback
from multiprocessing.connection import Connection
from pathlib import Path
from typing import Any

from robot_api import EpisodeOver, Image, Robot
from robot_world.loader import ProgramLoadError, load_program
from robot_world.runner import EpisodeResult
from robot_world.sim import Outcome, Simulation
from robot_world.sim_robot import SimRobot
from robot_world.world import World

COMMANDS = frozenset({"forward", "backward", "turn", "look", "heading", "say"})


class RemoteRobot(Robot):
    """The program's view of the robot: every command is a round trip over the pipe."""

    def __init__(self, conn: Connection) -> None:
        self._conn = conn

    def _call(self, name: str, *args: Any) -> Any:
        self._conn.send(("call", name, args))
        reply = self._conn.recv()
        if reply[0] == "over":
            raise EpisodeOver(reply[1])
        return reply[1]

    def forward(self, distance: float) -> float:
        return self._call("forward", distance)

    def backward(self, distance: float) -> float:
        return self._call("backward", distance)

    def turn(self, degrees: float) -> None:
        self._call("turn", degrees)

    def look(self) -> Image:
        return self._call("look")

    def heading(self) -> float:
        return self._call("heading")

    def say(self, message: str) -> None:
        self._call("say", message)


def _child_main(conn: Connection, wheel: str) -> None:
    try:
        program = load_program(Path(wheel))
    except ProgramLoadError as exc:
        conn.send(("error", str(exc)))
        return
    conn.send(("ready",))
    try:
        program(RemoteRobot(conn))
        _send_quietly(conn, ("done",))
    except EpisodeOver:
        _send_quietly(conn, ("done",))
    except Exception:
        _send_quietly(conn, ("error", traceback.format_exc()))


def _send_quietly(conn: Connection, message: tuple) -> None:
    """Send, ignoring a pipe the parent has already closed (it has stopped listening)."""
    with contextlib.suppress(OSError, EOFError):
        conn.send(message)


def run_wheel(
    world: World,
    wheel: Path,
    *,
    wall_timeout: float = 30.0,
    startup_timeout: float = 120.0,
    **sim_options: Any,
) -> EpisodeResult:
    """Run the program in ``wheel`` through one episode of ``world`` in a subprocess.

    ``wall_timeout`` is how long, in real seconds, the program may go without sending a
    command before it is declared stuck and killed. ``startup_timeout`` is how long the
    subprocess may take to start and load the wheel. ``sim_options`` go to
    :class:`Simulation`.
    """
    context = multiprocessing.get_context("spawn")
    parent_conn, child_conn = context.Pipe()
    process = context.Process(target=_child_main, args=(child_conn, str(wheel)), daemon=True)
    process.start()
    child_conn.close()

    sim = Simulation(world, **sim_options)
    robot = SimRobot(sim)
    error = None
    timeout = startup_timeout
    try:
        while True:
            if not parent_conn.poll(timeout):
                error = f"the program did not send a command for {timeout} s"
                sim.end(Outcome.STUCK)
                break
            message = parent_conn.recv()
            if message[0] == "ready":
                timeout = wall_timeout
                continue
            if message[0] == "call":
                _, name, args = message
                if name not in COMMANDS:
                    error = f"unknown robot command {name!r}"
                    sim.end(Outcome.ERROR)
                    break
                try:
                    parent_conn.send(("ok", getattr(robot, name)(*args)))
                except EpisodeOver as over:
                    parent_conn.send(("over", over.outcome))
                    break
            elif message[0] == "done":
                sim.end(Outcome.FINISHED)
                break
            else:
                error = message[1]
                sim.end(Outcome.ERROR)
                break
    finally:
        parent_conn.close()
        process.join(timeout=2.0)
        if process.is_alive():
            process.terminate()
            process.join()
    return EpisodeResult(sim.outcome, sim.time, sim.recording, error)
