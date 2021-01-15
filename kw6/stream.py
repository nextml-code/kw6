from pathlib import Path
from pydantic import BaseModel

from kw6 import Position

N_BYTES_DOUBLE = 8


class Stream(BaseModel):
    '''
    Used to iterate over images in a kw6 file.

    Example:

    .. code-block:: python

        from pathlib import Path
        import kw6

        path = Path('...')

        for position in kw6.Stream(path):
            for camera in position.cameras:
                camera.image.save(
                    f'{position.header.frame_index}_{camera.header.camera_index}.png'
                )
    '''

    path: Path

    class Config:
        allow_mutation = False

    def __init__(self, path):
        super().__init__(path=path)

    @property
    def version(self):
        '''kw6 file format version'''
        with self.path.open('rb') as stream:
            return Stream.version_(stream)

    @staticmethod
    def version_(stream):
        return stream.read(19).decode().strip()

    def __iter__(self):
        '''Iterate over positions and cameras in the file'''
        with self.path.open('rb') as stream:
            if Stream.version_(stream) != 'KW6FileClassVer1.0':
                raise ValueError(f'Unexpected file version {self.version}')

            while stream.peek(1) != b'':
                yield Position.from_stream_(stream)


def test_file_not_found():
    import pytest

    with pytest.raises(FileNotFoundError):
        Stream('fail').version


def test_iter():
    import pytest

    max_position = 0
    with pytest.raises(ValueError):
        for position in Stream('test/test.kw6'):
            max_position = position.header.frame_index

    assert max_position >= 50
