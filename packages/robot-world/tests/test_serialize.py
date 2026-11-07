import base64
import struct
import zlib

import numpy as np
import pytest

from robot_api import Robot
from robot_world.png import encode_png
from robot_world.runner import run_program
from robot_world.serialize import episode_to_dict


def decode_png(data: bytes) -> tuple[int, int, np.ndarray]:
    """A minimal decoder for the PNGs we write: 8-bit RGB, no interlace, filter 0."""
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    pos = 8
    width = height = 0
    idat = b""
    while pos < len(data):
        (length,) = struct.unpack(">I", data[pos : pos + 4])
        kind = data[pos + 4 : pos + 8]
        body = data[pos + 8 : pos + 8 + length]
        (crc,) = struct.unpack(">I", data[pos + 8 + length : pos + 12 + length])
        assert crc == zlib.crc32(kind + body)
        if kind == b"IHDR":
            width, height, depth, color = struct.unpack(">IIBB", body[:10])
            assert (depth, color) == (8, 2)
        elif kind == b"IDAT":
            idat += body
        pos += 12 + length
    raw = zlib.decompress(idat)
    stride = width * 3 + 1
    rows = [raw[i * stride : (i + 1) * stride] for i in range(height)]
    assert all(row[0] == 0 for row in rows)
    pixels = np.frombuffer(b"".join(row[1:] for row in rows), dtype=np.uint8)
    return width, height, pixels.reshape(height, width, 3)


def test_png_round_trips_pixels():
    image = np.zeros((3, 5, 3), dtype=np.uint8)
    image[1, 2] = (255, 0, 128)
    image[2, 4] = (1, 2, 3)
    width, height, decoded = decode_png(encode_png(image))
    assert (width, height) == (5, 3)
    assert np.array_equal(decoded, image)


def test_png_rejects_bad_shapes():
    with pytest.raises(ValueError):
        encode_png(np.zeros((3, 5), dtype=np.uint8))


def test_episode_to_dict_is_json_friendly(goal_ahead_world):
    def program(robot: Robot) -> None:
        robot.say("off we go")
        robot.look()
        robot.forward(10.0)

    result = run_program(goal_ahead_world, program, dt=0.5)
    data = episode_to_dict(goal_ahead_world, result)

    assert data["outcome"] == "success"
    assert data["time"] == pytest.approx(3.1)
    assert data["error"] is None
    assert data["world"]["width"] == 20.0
    assert data["world"]["patches"][0]["terrain"] == "goal"

    frames = data["frames"]
    assert frames[0] == [0.0, 5.0, 5.0, 0.0]
    assert frames[1] == [0.1, 5.0, 5.0, 0.0]  # the look
    assert frames[-1][0] == pytest.approx(3.1)
    assert frames[-1][1] == pytest.approx(8.0)
    assert all(len(frame) == 4 for frame in frames)

    assert data["messages"] == [[0, "off we go"]]
    (look,) = data["looks"]
    assert look["frame"] == 1
    width, height, pixels = decode_png(base64.b64decode(look["png"]))
    assert (width, height) == (128, 96)
    assert np.array_equal(pixels, result.recording.looks[0].image)


def test_episode_to_dict_includes_error_text(goal_ahead_world):
    def program(robot: Robot) -> None:
        raise RuntimeError("bang")

    data = episode_to_dict(goal_ahead_world, run_program(goal_ahead_world, program))
    assert data["outcome"] == "error"
    assert "RuntimeError: bang" in data["error"]


def test_episode_summary_has_the_verdict_but_no_frames_or_pictures(goal_ahead_world):
    from robot_world.runner import run_program
    from robot_world.serialize import episode_summary

    def program(robot):
        robot.say("hello")
        robot.look()
        robot.forward(10.0)

    result = run_program(goal_ahead_world, program)
    summary = episode_summary(7, result)
    assert summary == {
        "seed": 7,
        "outcome": "success",
        "time": result.time,
        "error": None,
        "messages": ["hello"],
    }
