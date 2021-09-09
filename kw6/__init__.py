from kw6.reader import Reader

from pkg_resources import get_distribution, DistributionNotFound
try:
    __version__ = get_distribution("kw6").version
except DistributionNotFound:
    pass
