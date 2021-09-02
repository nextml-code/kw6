import io
import numpy as np
from collections.abc import Iterable
from xml.dom import minidom
from pathlib import Path
from pydantic import BaseModel, validate_arguments
from typing import Dict

from kw6 import Position, PositionHeader, types, settings, hdr


class Reader(BaseModel):
    """
    Used to iterate over images in a kw6 file.

    Example:

    .. code-block:: python

        from pathlib import Path
        import kw6

        path = Path("...")

        for position in kw6.Reader.from_path(path):
            for camera in position.cameras:
                camera.image.save(
                    f"{position.header.frame_index}_{camera.header.camera_index}.png"
                )
    """

    path: Path
    stream: io.BufferedReader
    cached_byte_positions: Dict[int, int]
    initial_frame_index: int

    class Config:
        arbitrary_types_allowed = True

    @staticmethod
    @validate_arguments
    def from_path(path: Path, header_path: Path = None):
        stream = path.open("rb")

        version = stream.read(settings.N_BYTES_VERSION).decode().strip()
        if version != "KW6FileClassVer1.0":
            raise ValueError(f"Unexpected file version {version}")

        initial_position_header = Position.skip_(stream)
        return Reader(
            path=path,
            stream=stream,
            cached_byte_positions=(
                hdr.positions(header_path)
                if header_path is not None
                else dict()
            ),
            initial_frame_index=initial_position_header.frame_index,
        )

    def empty(self):
        return self.stream.peek(1) == b""

    def __iter__(self):
        """Iterate over all positions and cameras in the file"""
        stream = self.path.open("rb")
        stream.seek(settings.N_BYTES_VERSION)
        while not stream.peek(1) == b"":
            byte_position = stream.tell()
            position = Position.from_stream_(stream)
            self.cached_byte_positions[position.header.frame_index] = byte_position
            yield position
        stream.close()

    def __len__(self):
        try:
            return self.assumptuous_length()
        except Exception:
            self.stream.seek(settings.N_BYTES_VERSION)
            if self.empty():
                return 0

            position_header = None
            while not self.empty():
                byte_position = self.stream.tell()
                position_header = Position.skip_(self.stream)
                self.cached_byte_positions[position_header.frame_index] = byte_position

            return position_header.frame_index - self.initial_frame_index + 1

    def assumptuous_length(self):
        self.stream.seek(settings.N_BYTES_VERSION)
        position_header = self.position_header()
        self.stream.seek(0, io.SEEK_END)
        end_position = self.stream.tell()
        assumptuous_length = (
            end_position - settings.N_BYTES_VERSION
        ) / position_header.n_frame_bytes

        if np.abs(assumptuous_length - np.round(assumptuous_length)) <= 1e-9:
            assumptuous_length = int(assumptuous_length)
        else:
            raise Exception(f"Unexpected length {assumptuous_length} of kw6 file")

        expected_frame_index = self.initial_frame_index + assumptuous_length - 1
        self.stream.seek(end_position - position_header.n_frame_bytes)
        position = Position.from_stream_(self.stream)
        if position.header.frame_index != expected_frame_index:
            raise Exception(
                f"Expected to find {expected_frame_index}, "
                f"but found {position.header.frame_index} instead."
            )
        return assumptuous_length

    def __getitem__(self, indices_or_slice):
        """
        Access a position by frame index. Supports slicing and array indexing

        Example:

        .. code-block:: python

            from pathlib import Path
            import kw6

            reader = kw6.Reader.from_path(Path("..."))
            position = reader[10]
            positions = reader[10:20]
            positions = reader[[5, 7, 9]]
        """
        if type(indices_or_slice) == int:
            positions = self.seek_position_(indices_or_slice)

        elif type(indices_or_slice) == slice:
            if indices_or_slice.start is None or indices_or_slice.stop is None:
                raise ValueError("NoneType not supported for slice start or stop")
            else:
                positions = [
                    self.seek_position_(index)
                    for index in range(
                        indices_or_slice.start,
                        indices_or_slice.stop,
                        indices_or_slice.step if indices_or_slice.step is not None else 1,
                    )
                ]

        elif isinstance(indices_or_slice, Iterable):
            positions = [self.seek_position_(index) for index in indices_or_slice]

        else:
            raise TypeError(f"Unindexable type {type(indices_or_slice)}")

        return positions

    def seek_position_(self, frame_index: types.FRAME_INDEX):
        if frame_index < 0:
            raise IndexError("Negative indexing not supported")

        if frame_index < self.initial_frame_index:
            raise IndexError(
                f"Frame index {frame_index} is smaller than the first frame "
                f"index {self.initial_frame_index}"
            )

        position = None
        step_size_confidence = -1
        while not self.empty():
            self.stream.seek(self.closest_stored_byte_position(frame_index))
            current_frame_index = PositionHeader.peek_from_stream(self.stream).frame_index
            try:
                if step_size_confidence == -1:
                    position = self.assumptuous_seek_position_(frame_index)
                else:
                    position = self.assumptuous_seek_position_(
                        min(current_frame_index + step_size_confidence, frame_index)
                    )
                    step_size_confidence *= 10
            except Exception:
                step_size_confidence = 1

            if position is not None and position.header.frame_index == frame_index:
                break

        if position is None or position.header.frame_index != frame_index:
            raise IndexError(f"Unable to find {frame_index}")

        return position

    def assumptuous_seek_position_(self, frame_index: types.FRAME_INDEX):
        self.stream.seek(self.closest_stored_byte_position(frame_index))
        position_header = self.position_header()

        byte_position = (
            position_header.n_frame_bytes * (frame_index - position_header.frame_index)
            + self.stream.tell()
        )
        if byte_position < 0:
            raise IndexError(
                f"Extrapolating to frame index {frame_index} gave a negative "
                "byte position"
            )

        self.stream.seek(byte_position)

        position = Position.from_stream_(self.stream)

        if position.header.frame_index != frame_index:
            raise IndexError(
                f"Expected to find {frame_index}, "
                f"but found {position.header.frame_index} instead."
            )

        self.cached_byte_positions[position.header.frame_index] = self.stream.tell()
        return position

    def closest_stored_byte_position(self, frame_index: types.FRAME_INDEX):
        available_positions = [
            position for position in self.cached_byte_positions.keys()
            if position <= frame_index
        ]
        if len(available_positions) > 0:
            return self.cached_byte_positions[max(available_positions)]
        else:
            return settings.N_BYTES_VERSION

    def close_(self):
        """Close the stream file object, makes the stream unusable"""
        self.stream.close()

    def position_header(self):
        return PositionHeader.peek_from_stream(self.stream)


def test_file_not_found():
    import pytest

    with pytest.raises(FileNotFoundError):
        Reader.from_path("fail").version


def test_iter():
    import pytest

    max_position = 0
    with pytest.raises(ValueError):
        for position in Reader.from_path("tests/constant_corrupt.kw6"):
            max_position = position.header.frame_index

    assert max_position >= 50


def test_indexing():
    reader = Reader.from_path("tests/constant_corrupt.kw6")
    assert reader[10].header.frame_index == 10
    assert reader[10:21][-1].header.frame_index == 20
    assert reader[[11, 5, 9]][1].header.frame_index == 5


def test_indexing_dynamic():
    reader = Reader.from_path("tests/dynamic.kw6")
    assert reader[2090].header.frame_index == 2090
    assert reader[2070].header.frame_index == 2070
    assert reader[2100].header.frame_index == 2100


def test_indexing_dynamic_header():
    reader = Reader.from_path("tests/dynamic.kw6", "tests/dynamic.hdr")
    assert reader[2090].header.frame_index == 2090
    assert reader[2070].header.frame_index == 2070
    assert reader[2100].header.frame_index == 2100


def test_length():
    reader = Reader.from_path("tests/constant.kw6")

    max_frame_index = 0
    for position in reader:
        max_frame_index = position.header.frame_index

    assert max_frame_index == reader.assumptuous_length() + reader.initial_frame_index - 1
    assert max_frame_index == len(reader) + reader.initial_frame_index - 1


def test_length_constant_corrupt():
    import pytest

    reader = Reader.from_path("tests/constant_corrupt.kw6")

    with pytest.raises(Exception):
        reader.assumptuous_length()


def test_length_dynamic():
    import pytest
    reader = Reader.from_path("tests/dynamic.kw6")

    with pytest.raises(Exception):
        reader.assumptuous_length()

    max_frame_index = None
    for position in reader:
        assert max_frame_index is None or position.header.frame_index == max_frame_index + 1
        max_frame_index = position.header.frame_index

    assert max_frame_index == len(reader) + reader.initial_frame_index - 1
