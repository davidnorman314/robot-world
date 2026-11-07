"""Runs a program through many seeds of a world, several episodes at a time.

A robot that works on one seed can fail on another, because the bridge, the goal and
the start move. Running a batch of seeds shows which ones it fails on, so each failure
can then be replayed in the viewer.
"""

import os
from collections.abc import Callable, Iterable, Iterator
from concurrent.futures import ThreadPoolExecutor, as_completed

from robot_world.runner import EpisodeResult
from robot_world.world import World

DEFAULT_WORKERS = min(4, os.cpu_count() or 1)


def run_batch(
    make_world: Callable[[int], World],
    run_episode: Callable[[World], EpisodeResult],
    seeds: Iterable[int],
    *,
    workers: int = DEFAULT_WORKERS,
) -> Iterator[tuple[int, EpisodeResult]]:
    """Yield ``(seed, result)`` for each seed as its episode finishes.

    Up to ``workers`` episodes run at once, so results arrive in finishing order, not
    seed order. Closing the iterator early cancels the episodes not yet started.
    """
    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        futures = {pool.submit(run_episode, make_world(seed)): seed for seed in seeds}
        try:
            for future in as_completed(futures):
                yield futures[future], future.result()
        finally:
            for future in futures:
                future.cancel()
