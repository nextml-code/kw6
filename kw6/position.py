import array
import numpy as np
from pydantic import BaseModel
from typing import Tuple

from kw6 import Camera, types, settings


class PositionHeader(BaseModel):
    n_frame_bytes: str
    camera_version: str
    frame_index: types.FRAME_INDEX
    time: str
    pulses: str
    n_active_cameras: int

    class Config:
        allow_mutation = False

    def peek(stream):
        names = PositionHeader.__fields__.keys()
        peek_length = settings.N_BYTES_DOUBLE * len(names)
        return PositionHeader(**dict(zip(
            names,
            array.array('d', stream.peek(peek_length)[:peek_length])
        )))

    @staticmethod
    def from_stream_(stream):
        names = PositionHeader.__fields__.keys()
        return PositionHeader(**dict(zip(
            names,
            array.array('d', stream.read(settings.N_BYTES_DOUBLE * len(names)))
        )))


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
        header = PositionHeader.from_stream_(stream)
        for i in range(header.n_active_cameras):
            Camera.skip_(stream)
