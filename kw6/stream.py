import io
from xml.dom import minidom
from pathlib import Path
from pydantic import BaseModel
from typing import Optional, List, Dict

from kw6 import Position, PositionHeader, types, settings


class Stream(BaseModel):
    '''
    Used to iterate over images in a kw6 file.

    Example:

    .. code-block:: python

        from pathlib import Path
        import kw6

        path = Path('...')

        for position in kw6.Stream.from_path(path):
            for camera in position.cameras:
                camera.image.save(
                    f'{position.header.frame_index}_{camera.header.camera_index}.png'
                )
    '''

    stream: io.BufferedReader
    cached_positions: Dict[int, int]

    class Config:
        allow_mutation = False
        arbitrary_types_allowed = True

    @staticmethod
    def from_path(path, header_path=None):
        stream = Path(path).open('rb')
        version = stream.read(settings.N_BYTES_VERSION).decode().strip()
        if version != 'KW6FileClassVer1.0':
            raise ValueError(f'Unexpected file version {version}')
        return Stream(
            stream=stream,
            cached_positions=header_positions(header_path) if header_path is not None else {},
        )

    def seek_(self, frame_index: types.FRAME_INDEX):
        '''Go to stream position indicated by frame_index'''

        self._seek_closest_stored_position(frame_index)

        if PositionHeader.peek(self.stream).frame_index > frame_index:
            print('WARNING: stream position ahead of input seek position, rewinding to start of file.')
            self.stream.seek(settings.N_BYTES_VERSION)

        while (
            self.stream.peek(1) != b''
            and PositionHeader.peek(self.stream).frame_index != frame_index
        ):
            Position.skip_(self.stream)

    def _seek_closest_stored_position(self, frame_index: types.FRAME_INDEX):
        available_positions = [
            position for position in self.cached_positions.keys()
            if position <= frame_index
        ]
        if len(available_positions) > 0:
            closest_position = min(
                available_positions,
                key=lambda position: frame_index - position,
            )
            self.stream.seek(self.cached_positions[closest_position])

    def read_positions_(self, n: int):
        '''Read n positions from current stream position'''
        for _ in range(n):
            if self.stream.peek(1) == b'':
                break
            else:
                yield Position.from_stream_(self.stream)

    def __iter__(self):
        '''Iterate over positions and cameras in the file from current stream position'''
        while self.stream.peek(1) != b'':
            yield Position.from_stream_(self.stream)

    def close_(self):
        self.stream.close()


def header_positions(path):
    def byte_position(position_data):
        return {
            position_info.split(' = ')[0]: int(position_info.split(' = ')[1].strip('"'))
            for position_info in position_data.firstChild.data.strip().split('\n')
        }
    return {
        position['kw6Pos']: position['kw6Byte']
        for position in map(
            byte_position,
            minidom.parse(str(path)).getElementsByTagName('kw6Index'),
        )
    }


def test_file_not_found():
    import pytest

    with pytest.raises(FileNotFoundError):
        Stream.from_path('fail').version


def test_iter():
    import pytest

    max_position = 0
    with pytest.raises(ValueError):
        for position in Stream.from_path('test/test.kw6'):
            max_position = position.header.frame_index

    assert max_position >= 50


def test_seek():
    stream = Stream.from_path('test/test.kw6')
    stream.seek_(10)
    stream.seek_(5)
    assert next(stream.read_positions_(1)).header.frame_index == 5
