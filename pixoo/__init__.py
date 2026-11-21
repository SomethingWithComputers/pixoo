from .__about__ import __version__
from .configurations.pixooconfiguration import PixooConfiguration
from .configurations.restconfiguration import RESTConfiguration
from .configurations.simulatorconfiguration import SimulatorConfiguration
from .constants.colors import Palette
from .enums.channel import Channel
from .enums.imageresamplemode import ImageResampleMode
from .enums.textscrolldirection import TextScrollDirection
from .extras.frameanimatedimage import FrameAnimatedImage
from .objects.pixoo import Pixoo, PixooConnectionError, PixooError, PixooResponseError

__all__ = (
    'Channel',
    'FrameAnimatedImage',
    'ImageResampleMode',
    'Palette',
    'Pixoo',
    'PixooConfiguration',
    'PixooConnectionError',
    'PixooError',
    'PixooResponseError',
    'PixooREST',
    'RESTConfiguration',
    'SimulatorConfiguration',
    'TextScrollDirection',
    '__version__',
)


def __getattr__(name):
    if name == 'PixooREST':
        from .objects.pixoorest import PixooREST

        return PixooREST

    raise AttributeError(f'module {__name__!r} has no attribute {name!r}')
