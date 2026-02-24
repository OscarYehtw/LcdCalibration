# 11/23/2020 claudeliao@
# 1. Add enum for brightness mode

"""
Copyright 2020 Google Inc. All Rights Reserved.
Author: claudeliao@
Last updated: 11/23/2020
"""

import enum


class ColorMode(enum.Enum):
    DEFAULT = 'DEFAULT'
    WIDE_COLOR_GAMUT = 'WIDE_COLOR_GAMUT'
    HDR = 'HDR'


class ColorSpace(enum.Enum):
    NATIVE = 'NATIVE'
    P3 = 'P3'
    SRGB = 'SRGB'
    BT2020 = 'BT2020'


class GammaCurve(enum.Enum):
    GAMMA22 = 'gamma22'
    SRGB_CURVE = 'srgb_curve'
    PQ_CURVE = 'pq_curve'


class BrightnessMode(enum.Enum):
    NORMAL = 'NORMAL'
    HBM = 'HIGH_BRIGHTNESS_MODE'


class Color(enum.Enum):
    WHITE = 'White'
    RED = 'Red'
    GREEN = 'Green'
    BLUE = 'Blue'
    CYAN = 'Cyan'
    MAGENTA = 'Magenta'
    YELLOW = 'Yellow'
    BLACK = 'Black'
    OTHER = 'other'

    def str(self):
        if self == self.WHITE:
            return 'W'
        elif self == self.RED:
            return 'R'
        elif self == self.GREEN:
            return 'G'
        elif self == self.BLUE:
            return 'B'
        elif self == self.CYAN:
            return 'C'
        elif self == self.MAGENTA:
            return 'M'
        elif self == self.YELLOW:
            return 'Y'
        elif self == self.BLACK:
            return 'K'
        else:
            return 'OTHER'


class PatternApk(enum.Enum):
    FIH = 'fih'
    OCTOPUS = 'octopus'
    FCT = 'b1_fct'


class InstrumentType(enum.Enum):
    Hyperion = 'Hyperion'
    CS2000 = 'CS2000'
    PRSeries = 'PRSeries'
