"""
Copyright 2020 Google Inc. All Rights Reserved.
Author: claudeliao@
Last updated: 10/28/2020
"""

import abc
import enum
import sys
import glob


def list_all_serial_ports():
    """ Lists serial port names

        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
    """
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    return ports


class Instrument(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def open(self):
        return NotImplemented

    @abc.abstractmethod
    def measure_XYZ(self):
        return NotImplemented

    @abc.abstractmethod
    def close(self):
        return NotImplemented


class BaudRate(enum.IntEnum):
    RATE_115200 = 115200
    RATE_57600 = 57600
    RATE_38400 = 38400
    RATE_19200 = 19200
    RATE_9600 = 9600
    RATE_4800 = 4800
    RATE_2400 = 2400
    RATE_1200 = 1200
    RATE_600 = 600


# CS2000
class DataMode(enum.Enum):
    MEASUREMENT_CONDITIONS = '0'
    SPECTRAL_DATA = '1'
    COLORIMETRIC_DATA = '2'


class ColorimetricDataType(enum.Enum):
    All_Colorimetric_Data = '00'
    XYZ = '01'
    xyL = '02'
    uvL = '03'
    X10Y10Z10 = '11'
    x10y10L = '12'
    u10v10L = '13'


class SpectralDataType(enum.Enum):
    from380to479nm = '01'
    from480to579nm = '02'
    from580to679nm = '03'
    from680to780nm = '04'
    from380to780nm = '05'


# PR Series
class DataCode(enum.Enum):
    Yxy = '1'
    XYZ = '2'
    Yuv = '3'
    Y_CCT_deviation = '4'
    spectral = '5'

