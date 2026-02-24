"""
Copyright 2020 Google Inc. All Rights Reserved.
Author: claudeliao@
Last updated: 10/28/2020
"""

import serial
import time
from ColorCalFramework.instrument import *


class PRSeries(Instrument):
    def __init__(self, com, baud_rate=BaudRate.RATE_9600):
        self.__ser = serial.Serial()
        self.__serial_port = com
        self.__baud_rate = baud_rate.value

    def open(self):
        try:
            self.__ser = serial.Serial(port=self.__serial_port, baudrate=self.__baud_rate, bytesize=serial.EIGHTBITS,
                                       stopbits=serial.STOPBITS_ONE, parity=serial.PARITY_NONE, timeout=1, rtscts=True)
            self.__ser.write(b'P')
            time.sleep(0.1)
            self.__ser.write(b'H')
            time.sleep(0.1)
            self.__ser.write(b'O')
            time.sleep(0.1)
            self.__ser.write(b'T')
            time.sleep(0.1)
            self.__ser.write(b'O')
            time.sleep(0.1)
            ret = self.__ser.readline().decode('utf-8')
            print(ret)
            if ret == ' REMOTE MODE':
                return True
            else:
                return False
        except Exception as e:
            print(e)

    def is_open(self):
        try:
            return self.__ser.is_open
        except Exception as e:
            print(e)

    def close(self):
        try:
            self.__ser.write(b'Q')
            self.__ser.close()
        except Exception as e:
            print(e)

    def measure_data(self, data_code=DataCode.XYZ):
        try:
            retry = 30
            self.__ser.write(b'M')
            time.sleep(0.1)
            self.__ser.write(data_code.value.encode('utf-8'))
            time.sleep(0.1)
            self.__ser.write(b'\r')
            time.sleep(0.1)

            for _ in range(retry):
                ret = self.__ser.readlines()
                time.sleep(0.5)
                print('Waiting measurement...')
                if len(ret) != 0:
                    if '0000' in ret[0].decode('utf-8'):
                        print('Measurement is done')
                        return True
            return False
        except Exception as e:
            print(e)

    def read_measured_data(self, data_code=DataCode.XYZ):
        try:
            self.__ser.write(b'D')
            time.sleep(0.1)
            self.__ser.write(data_code.value.encode('utf-8'))
            time.sleep(0.1)
            self.__ser.write(b'\r')
            time.sleep(0.1)

            if data_code == DataCode.spectral:
                ret = self.__ser.readlines()[1:]
                return [float(j) for i in ret for j in i.decode('utf-8').replace('\r\n', '').split(',')]
            elif data_code == DataCode.XYZ:
                ret = self.__ser.read_until(b'\r\n').decode('utf-8').replace('\r\n', '').split(',')[2:]
                return [float(i)/3.426 for i in ret]
            else:
                ret = self.__ser.read_until(b'\r\n').decode('utf-8').replace('\r\n', '').split(',')[2:]
                return [float(i) for i in ret]
        except Exception as e:
            print(e)

    def measure_XYZ(self):
        self.measure_data()
        return self.read_measured_data()


def main():
    com_port = list_all_serial_ports()[2]
    print(com_port)
    pr670 = PRSeries(com_port)
    pr670.open()

    if pr670.is_open():
        if pr670.measure_data():
            print(pr670.read_measured_data(data_code=DataCode.XYZ))
            print(pr670.read_measured_data(data_code=DataCode.Yxy))
            print(pr670.read_measured_data(data_code=DataCode.Yuv))
            print(pr670.read_measured_data(data_code=DataCode.spectral))

    pr670.close()
    print(pr670.is_open())


if __name__ == '__main__':
    main()
