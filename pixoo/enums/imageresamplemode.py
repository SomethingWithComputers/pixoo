from enum import IntEnum

from PIL import Image


class ImageResampleMode(IntEnum):
    PIXEL_ART = Image.Resampling.NEAREST
    SMOOTH = Image.Resampling.LANCZOS
