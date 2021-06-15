import io
from collections.abc import Iterable
from xml.dom import minidom
from pathlib import Path
from pydantic import BaseModel
from typing import Dict

from kw6 import Position, PositionHeader, types, settings


class Reader(BaseModel):
    '''
    Used to iterate over images in a kw6 file.

    Example:

    .. code-block:: python

        from pathlib import Path
        import kw6

        path = Path('...')

        for position in kw6.Reader.from_path(path):
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
        return Reader(
            stream=stream,
            cached_positions=header_positions(header_path) if header_path is not None else {},
        )

    def __getitem__(self, indices_or_slice):
        '''
        Access a position by frame index. Supports slicing and array indexing
        
        Example:

        .. code-block:: python

            from pathlib import Path
            import kw6

            reader = kw6.Reader.from_path(Path('...'))
            position = reader[10]
            positions = reader[10: 20]
            positions = reader[[5, 7, 9]]
            all_positions = reader[:]
        '''
        if type(indices_or_slice) == int:
            if indices_or_slice < 0:
                raise IndexError('Negative indexing not supported.')
            self.seek_(indices_or_slice)
            if not self.empty():
                positions = Position.from_stream_(self.stream)
            else:
                raise IndexError(indices_or_slice)

        elif type(indices_or_slice) == slice:
            if indices_or_slice.start is None or indices_or_slice.stop is None:
                raise ValueError('NoneType not supported for slice start or stop')
            else:
                positions = [
                    self[index]
                    for index in range(
                        indices_or_slice.start,
                        indices_or_slice.stop,
                        indices_or_slice.step if indices_or_slice.step is not None else 1,
                    )
                ]

        elif isinstance(indices_or_slice, Iterable):
            positions = [self[index] for index in indices_or_slice]

        else:
            raise TypeError(f'Unindexable type {type(indices_or_slice)}')

        return positions

    def empty(self):
        return self.stream.peek(1) == b''

    def seek_(self, frame_index: types.FRAME_INDEX):
        '''Move the stream position to the position indicated by frame_index'''
        if frame_index in self.cached_positions:
            self.stream.seek(self.cached_positions[frame_index])
        else:
            self.stream.seek(self.closest_stored_position(frame_index))
            while not self.empty():
                next_position = PositionHeader.peek(self.stream).frame_index
                self.cached_positions[next_position] = self.stream.tell()
                if next_position != frame_index:
                    Position.skip_(self.stream)
                else:
                    break

    def closest_stored_position(self, frame_index: types.FRAME_INDEX):
        available_positions = [
            position for position in self.cached_positions.keys()
            if position <= frame_index
        ]
        if len(available_positions) > 0:
            return self.cached_positions[max(available_positions)]
        else:
            return settings.N_BYTES_VERSION

    def __iter__(self):
        '''Iterate over all positions and cameras in the file'''
        self.stream.seek(settings.N_BYTES_VERSION)
        while not self.empty():
            stream_position = self.stream.tell()
            position = Position.from_stream_(self.stream)
            self.cached_positions[position.header.frame_index] = stream_position
            yield position

    def close_(self):
        '''Close the stream file object, makes the stream unusable'''
        self.stream.close()


def header_positions(path):
    def byte_position(position_data):
        return {
            position_info.split(' = ')[0]: int(position_info.split(' = ')[1].strip('"'))
            for position_info in position_data.firstChild.data.strip().split('\n')
        }
    return {
        position['kw6Pos'] // 10: position['kw6Byte']
        for position in map(
            byte_position,
            minidom.parse(str(path)).getElementsByTagName('kw6Index'),
        )
    }


def test_file_not_found():
    import pytest

    with pytest.raises(FileNotFoundError):
        Reader.from_path('fail').version


def test_iter():
    import pytest

    max_position = 0
    with pytest.raises(ValueError):
        for position in Reader.from_path('test/test.kw6'):
            max_position = position.header.frame_index

    assert max_position >= 50


def test_indexing():
    reader = Reader.from_path('test/test.kw6')
    assert reader[10].header.frame_index == 10
    assert reader[10: 21][-1].header.frame_index == 20
    assert reader[[11, 5, 9]][1].header.frame_index == 5
