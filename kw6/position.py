from __future__ import annotations

import array
from typing import Any, BinaryIO, Tuple

from pydantic import BaseModel

from kw6 import settings, types
from kw6.camera import Camera


class PositionHeader(BaseModel):
    n_frame_bytes: int
    camera_version: str
    frame_index: types.FRAME_INDEX
    time: str
    pulses: str
    n_active_cameras: int

    class Config:
        allow_mutation = False

    @staticmethod
    def peek_from_stream(stream: BinaryIO) -> PositionHeader:
        """
        Peek at the stream and create a PositionHeader without advancing the stream pointer.

        Args:
            stream: A binary stream to peek from.

        Returns:
            A PositionHeader object created from the peeked bytes.
        """
        byte_size = PositionHeader.byte_size()
        return PositionHeader.from_bytes(stream.peek(byte_size)[:byte_size])

    @staticmethod
    def from_stream_(stream: BinaryIO) -> PositionHeader:
        """
        Create a PositionHeader from a binary stream.

        Args:
            stream: A binary stream to read from.

        Returns:
            A PositionHeader object created from the read bytes.
        """
        return PositionHeader.from_bytes(stream.read(PositionHeader.byte_size()))

    @staticmethod
    def from_bytes(bytes: bytes) -> PositionHeader:
        """
        Create a PositionHeader from bytes.

        Args:
            bytes: A bytes object containing the PositionHeader data.

        Returns:
            A PositionHeader object created from the input bytes.
        """
        values = array.array("d", bytes)
        return PositionHeader(
            n_frame_bytes=int(values[0]),
            camera_version=str(int(values[1])),
            frame_index=int(values[2]),
            time=str(values[3]),
            pulses=str(int(values[4])),
            n_active_cameras=int(values[5]),
        )

    @staticmethod
    def byte_size() -> int:
        """
        Calculate the byte size of the PositionHeader.

        Returns:
            The size of the PositionHeader in bytes.
        """
        names = PositionHeader.__fields__.keys()
        return settings.N_BYTES_DOUBLE * len(names)


class Position(BaseModel):
    header: PositionHeader
    cameras: Tuple[Camera, ...]

    class Config:
        allow_mutation = False

    @staticmethod
    def from_stream_(stream: BinaryIO) -> Position:
        """
        Create a Position object from a binary stream.

        Args:
            stream: A binary stream to read from.

        Returns:
            A Position object created from the read data.
        """
        header = PositionHeader.from_stream_(stream)
        return Position(
            header=header,
            cameras=tuple(
                Camera.from_stream_(stream) for _ in range(header.n_active_cameras)
            ),
        )

    @staticmethod
    def skip_(stream: BinaryIO) -> PositionHeader:
        """
        Skip the current position in the stream and return its header.

        Args:
            stream: A binary stream to skip in.

        Returns:
            The PositionHeader of the skipped position.
        """
        header = PositionHeader.peek_from_stream(stream)
        stream.seek(stream.tell() + header.n_frame_bytes)
        return header
