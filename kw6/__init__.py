from kw6 import settings
from kw6 import types
from kw6.camera import Camera, CameraHeader
from kw6.position import Position, PositionHeader
from kw6.stream import Stream
from kw6.to_png import to_png

from pkg_resources import get_distribution, DistributionNotFound
try:
    __version__ = get_distribution('kw6').version
except DistributionNotFound:
    pass
