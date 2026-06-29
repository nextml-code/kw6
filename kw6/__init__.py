from kw6.reader import Reader

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("kw6")
except PackageNotFoundError:
    pass
