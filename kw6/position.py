import array
from pydantic import BaseModel
from typing import Tuple

from kw6 import Camera, types, settings


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
    def peek_from_stream(stream):
        byte_size = PositionHeader.byte_size()
        return PositionHeader(**dict(zip(
            PositionHeader.__fields__.keys(),
            array.array("d", stream.peek(byte_size)[:byte_size]),
        )))

    @staticmethod
    def from_stream_(stream):
        return PositionHeader(**dict(zip(
            PositionHeader.__fields__.keys(),
            array.array("d", stream.read(PositionHeader.byte_size()))
        )))

    @staticmethod
    def byte_size():
        names = PositionHeader.__fields__.keys()
        return settings.N_BYTES_DOUBLE * len(names)


class Position(BaseModel):
    header: PositionHeader
    cameras: Tuple[Camera, ...]

    class Config:
        allow_mutation = False

    @staticmethod
    def from_stream_(stream):
        header = PositionHeader.from_stream_(stream)
        return Position(
            header=header,
            cameras=tuple(
                Camera.from_stream_(stream)
                for _ in range(header.n_active_cameras)
            )
        )

    @staticmethod
    def skip_(stream):
        header = PositionHeader.peek_from_stream(stream)
        stream.seek(stream.tell() + header.n_frame_bytes)
        return header
