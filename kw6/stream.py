import io
from pathlib import Path
from pydantic import BaseModel

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

    class Config:
        allow_mutation = False
        arbitrary_types_allowed = True

    @staticmethod
    def from_path(path):
        stream = Path(path).open('rb')
        version = stream.read(settings.N_BYTES_VERSION).decode().strip()
        if version != 'KW6FileClassVer1.0':
            raise ValueError(f'Unexpected file version {version}')
        return Stream(stream=stream)

    def seek_(self, frame_index: types.FRAME_INDEX):
        '''Go to stream position indicated by frame_index'''
        if PositionHeader.peek(self.stream).frame_index > frame_index:
            print('WARNING: stream position ahead of input seek position, rewinding to start of file.')
            self.stream.seek(settings.N_BYTES_VERSION)
        while (
            PositionHeader.peek(self.stream).frame_index != frame_index
            and self.stream.peek(1) != b''
        ):
            Position.skip_(self.stream)

    def read_positions_(self, n: int):
        '''Read n positions from current stream position'''
        for i in range(n):
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
