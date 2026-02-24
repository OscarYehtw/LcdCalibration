"""
Copyright 2020 Google Inc. All Rights Reserved.
Author: claudeliao@
Last updated: 10/28/2020
"""

import pyvisa as visa
from ColorCalFramework.instrument import *
import threading
import time


def decode_uni(uni_res):
    dec_res = str(uni_res).split(',')
    return dec_res


class MeasurementType(enum.Enum):
    XYZ = 'XYZ'
    Yxy = 'Yxy'
    Yuv = 'Yuv'
    Y = 'Y'
    DWL = 'DWL'
    Flicker = 'FLICker'


# +++++++++++++
class Hyperion(Instrument):
    def __init__(self, usb_port=None):
        self.__hyperion = None
        self.__usb_port = usb_port

    def open(self):
        try:
            rm = visa.ResourceManager()
            print('1st ResourceManager()')
        except Exception as e:
            print('[ERROR] {}'.format(e))
            print('[ERROR] {}'.format(e))
            print('[ERROR] {}'.format(e))
        try:
            if rm is None:
                rm = visa.ResourceManager()
                print('2nd ResourceManager()')

            if self.__usb_port is None:
                usb_list = rm.list_resources('USB?*23CF?*')
                self.__hyperion = rm.open_resource(usb_list[0])
            else:
                self.__hyperion = rm.open_resource(self.__usb_port)
            self.__hyperion.timeout = 5000
        except Exception as e:
            print('[ERROR] {}'.format(e))
            print('[ERROR] {}'.format(e))
            print('[ERROR] {}'.format(e))

    def measure(self, measurement_type=MeasurementType.XYZ, sbw='factory', frequency=60.0, frames=1, method=2, sample=4000, delay=0):
        try:
            print(self.__hyperion.query(':*IDN?'))

            print(self.__hyperion.query(':SENSe:SBW?\n'))
            self.__hyperion.write(':SENSe:SBW %s\n' % sbw)
            print(self.__hyperion.query(':SENSe:SBW?\n'))

            print('Auto-range (before): ')
            print(self.__hyperion.query(':SENSe:AUTORANGE?\n'))
            self.__hyperion.write(':SENSe:AUTORANGE 1\n')
            print('Auto-range (after): ')
            print(self.__hyperion.query(':SENSe:AUTORANGE?\n'))

            self.__hyperion.write(':SENSe:AUTOPARMS %d,%d,20\n' % (frequency, frames))

            if measurement_type == MeasurementType.Flicker:
                res = self.__hyperion.query(':measure:%s %d,%d,%d\n' % (measurement_type.value, method, sample, delay))
            else:
                res = self.__hyperion.query(':measure:%s\n' % measurement_type.value)
            res_decoded = decode_uni(res)
            res_list = [float(x) for x in res_decoded]
            if measurement_type == MeasurementType.Flicker:
                return res_list[0]
            else:
                for i in range(3):
                    if res_list[i] < 0:
                        res_list[i] = 0
                return res_list[0:3]
        except Exception as e:
            print(e)

    def measure_XYZ(self, sbw='factory', frequency=60.0, frames=1, method=2, sample=4000, delay=0):
        return self.measure(MeasurementType.XYZ, sbw, frequency, frames, method, sample)

    def close(self):
        try:
            self.__hyperion.close()
        except Exception as e:
            print(e)


def main():
    hyperion = Hyperion()
    hyperion.open()
    print(hyperion.measure())
    hyperion.close()


def measure(hyperion, times):
    hyperion.open()
    for i in range(times):
        print(hyperion.measure())
        time.sleep(1)
    hyperion.close()


class MyThread(threading.Thread):
    def __init__(self, hyperion, times):
        threading.Thread.__init__(self)
        self.hyperion = hyperion
        self.times = times

    def run(self):
        print("Start thread：" + self.name)
        measure(self.hyperion, self.times)
        print("End thread：" + self.name)


def main_multi_up():

    rm = visa.ResourceManager()
    usb_list = rm.list_resources('USB?*23CF?*')
    print(usb_list)

    hyperion_list = [Hyperion(usb_port=usb) for usb in usb_list]
    thread_list = []

    for hyperion in hyperion_list:
        thread_list.append(MyThread(hyperion, 5))
    for thread in thread_list:
        thread.start()
    # for thread in thread_list:
    #     thread.join()


if __name__ == '__main__':
    main()
    # main_multi_up()
