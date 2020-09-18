from pathlib import Path
from pydantic import BaseModel

from kw6 import Position

N_BYTES_DOUBLE = 8


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
        return stream.read(19).decode().strip()

    def __iter__(self):
        with self.path.open('rb') as stream:
            if Stream.version_(stream) != 'KW6FileClassVer1.0':
                raise ValueError(f'Unexpected file version {self.version}')

            while stream.peek(1) != b'':
                yield Position.from_stream_(stream)
