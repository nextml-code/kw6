import array
import io

import numpy as np
from PIL import Image
from pydantic import BaseModel

from kw6 import settings, types


class CameraHeader(BaseModel):
    camera_version: int
    camera_index: types.CAMERA_INDEX
    scale_height: float
    scale_length: float
    xMM: float
    yMM: float
    xPixC: float
    yPixC: float
    sub_sample: float
    expoMS: float
    x0: float
    y0: float
    width: int
    height: int
    _10xReserved: float
    _5xWearLeft: float
    _5xWearRight: float

    class Config:
        allow_mutation = False

    @staticmethod
    def from_stream_(stream):
        names = CameraHeader.__fields__.keys()
        values = array.array("d", stream.read(CameraHeader.byte_size()))
        parsed_values = []
        for name, value in zip(names, values):
            if name in [
                "camera_version",
                "scale_height",
                "scale_length",
                "xMM",
                "yMM",
                "xPixC",
                "yPixC",
                "sub_sample",
                "expoMS",
                "x0",
                "y0",
            ]:
                parsed_values.append(str(value))
            elif name in ["camera_index", "width", "height"]:
                parsed_values.append(int(value))
            else:
                parsed_values.append(value)
        return CameraHeader(**dict(zip(names, parsed_values)))

    @staticmethod
    def from_bytes(bytes):
        names = CameraHeader.__fields__.keys()
        return CameraHeader(
            **dict(zip(names, array.array("d", bytes[: CameraHeader.byte_size()])))
        )

    @staticmethod
    def byte_size():
        names = CameraHeader.__fields__.keys()
        return settings.N_BYTES_DOUBLE * len(names)


class Camera(BaseModel):
    header: CameraHeader
    image: Image.Image

    class Config:
        arbitrary_types_allowed = True
        allow_mutation = False

    @staticmethod
    def from_stream_(stream):
        header = CameraHeader.from_stream_(stream)
        return Camera(
            header=header,
            image=Camera.image_(stream, header),
        )

    @staticmethod
    def image_(stream, header):
        n_rows = header.height
        n_cols = header.width
        stream.read(
            settings.N_BYTES_DOUBLE * (settings.IM_HDR_SIZE - len(header.dict()))
        )

        image_data = np.array(array.array("B", stream.read(n_rows * n_cols))).reshape(
            n_rows, n_cols
        )

        return Image.fromarray(image_data)

    @staticmethod
    def skip_(stream):
        header = CameraHeader.from_stream_(stream)
        stream.seek(Camera.byte_size(header) - CameraHeader.byte_size(), io.SEEK_CUR)
        return header

    @staticmethod
    def byte_size(header):
        return (
            CameraHeader.byte_size()
            + settings.N_BYTES_DOUBLE * (settings.IM_HDR_SIZE - len(header.dict()))
            + header.height * header.width
        )
