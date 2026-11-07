"""Runs a robot program through one episode and reports what happened."""

import traceback
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from robot_api import EpisodeOver, Robot
from robot_world.sim import Outcome, Recording, Simulation
from robot_world.sim_robot import SimRobot
from robot_world.world import World

Program = Callable[[Robot], None]


@dataclass
class EpisodeResult:
    outcome: Outcome
    time: float
    recording: Recording
    error: str | None = None

    @property
    def succeeded(self) -> bool:
        return self.outcome is Outcome.SUCCESS


def run_program(world: World, program: Program, **sim_options: Any) -> EpisodeResult:
    """Run ``program`` in this process against a fresh simulation of ``world``.

    ``sim_options`` are passed to :class:`Simulation`.
    """
    sim = Simulation(world, **sim_options)
    error = None
    try:
        program(SimRobot(sim))
        sim.end(Outcome.FINISHED)
    except EpisodeOver:
        pass
    except Exception:
        error = traceback.format_exc()
        sim.end(Outcome.ERROR)
    return EpisodeResult(sim.outcome, sim.time, sim.recording, error)
