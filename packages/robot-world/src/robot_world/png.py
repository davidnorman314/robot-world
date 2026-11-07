"""A tiny PNG encoder for camera images, so the viewer needs no image library."""

import struct
import zlib

import numpy as np


def _chunk(kind: bytes, body: bytes) -> bytes:
    return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body))


def encode_png(image: np.ndarray) -> bytes:
    """Encode an ``(height, width, 3)`` uint8 array as an 8-bit RGB PNG."""
    if image.ndim != 3 or image.shape[2] != 3:
        raise ValueError(f"image must have shape (height, width, 3), got {image.shape}")
    image = np.ascontiguousarray(image, dtype=np.uint8)
    height, width, _ = image.shape
    filter_bytes = np.zeros((height, 1), dtype=np.uint8)
    raw = np.hstack([filter_bytes, image.reshape(height, width * 3)]).tobytes()
    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", header)
        + _chunk(b"IDAT", zlib.compress(raw))
        + _chunk(b"IEND", b"")
    )
