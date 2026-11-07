"""Turns an episode into plain JSON-friendly data for the browser viewer."""

import base64
from typing import Any

from robot_world.png import encode_png
from robot_world.runner import EpisodeResult
from robot_world.world import World


def episode_to_dict(world: World, result: EpisodeResult) -> dict[str, Any]:
    """Everything the viewer needs to replay an episode.

    ``frames`` is a list of ``[time, x, y, heading]`` per simulation tick. ``looks`` are
    the camera images as base64 PNGs, each tagged with the frame it was taken at.
    ``messages`` are ``[frame, text]`` pairs from ``robot.say``.
    """
    recording = result.recording
    return {
        "world": world.to_dict(),
        "outcome": result.outcome.value,
        "time": result.time,
        "error": result.error,
        "frames": [[f.time, f.pose.x, f.pose.y, f.pose.heading] for f in recording.frames],
        "looks": [
            {"frame": look.frame, "png": base64.b64encode(encode_png(look.image)).decode("ascii")}
            for look in recording.looks
        ],
        "messages": [[frame, text] for frame, text in recording.messages],
    }
