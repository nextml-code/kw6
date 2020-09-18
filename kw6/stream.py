from pathlib import Path
import array
import numpy as np
import PIL.Image
from pydantic import BaseModel
from typing import Tuple

N_BYTES_DOUBLE = 8


class ImageHeader(BaseModel):
    camera_version: str
    camera_index: str
    scale_height: str
    scale_length: str
    xMM: str
    yMM: str
    xPixC: str
    yPixC: str
    sub_sample: str
    expoMS: str
    x0: str
    y0: str
    width: int
    height: int
    _10xReserved: str
    _5xWearLeft: str
    _5xWearRight: str

    def from_stream_(stream):
        names = ImageHeader.__fields__.keys()
        return ImageHeader(**dict(zip(
            names,
            array.array('d', stream.read(N_BYTES_DOUBLE * len(names)))
        )))


class Image(BaseModel):
    header: ImageHeader
    image: PIL.Image.Image

    class Config:
        arbitrary_types_allowed = True
        allow_mutation = False

    @staticmethod
    def from_stream_(stream):
        header = ImageHeader.from_stream_(stream)
        return Image(
            header=header,
            image=Image.image_(stream, header),
        )

    @staticmethod
    def image_(stream, header):
        im_hdr_size = 34

        n_rows = header.height
        n_cols = header.width
        stream.read(N_BYTES_DOUBLE * (im_hdr_size - len(header.dict())))

        image_data = np.array(
            array.array('B', stream.read(n_rows * n_cols))
        ).reshape(n_rows, n_cols)

        return PIL.Image.fromarray(image_data)


class PositionHeader(BaseModel):
    n_frame_bytes: str
    camera_version: str
    frame_index: str
    time: str
    pulses: str
    n_active_cameras: int

    @staticmethod
    def from_stream_(stream):
        names = PositionHeader.__fields__.keys()
        return PositionHeader(**dict(zip(
            names,
            array.array('d', stream.read(N_BYTES_DOUBLE * len(names)))
        )))


class Position(BaseModel):
    header: PositionHeader
    images: Tuple[Image, ...]

    @staticmethod
    def from_stream_(stream):
        header = PositionHeader.from_stream_(stream)
        return Position(
            header=header,
            images=tuple(
                Image.from_stream_(stream)
                for _ in range(header.n_active_cameras)
            )
        )


class Stream(BaseModel):
    path: Path

    def __init__(self, path):
        super().__init__(path=path)

    @property
    def version(self):
        with self.path.open('rb') as stream:
            return Stream.version_(stream)

    @staticmethod
    def version_(stream):
        return stream.read(19)

    def __iter__(self):
        with self.path.open('rb') as stream:
            Stream.version_(stream)

            while stream.peek(1) != b'':
                yield Position.from_stream_(stream)
