"""
Copyright 2020 Google Inc. All Rights Reserved.
Author: claudeliao@
Last updated: 10/28/2020
"""

import serial
import struct
from ColorCalFramework.instrument import *


class CS2000(Instrument):
    def __init__(self, com, baud_rate=BaudRate.RATE_115200):
        self.__ser = serial.Serial()
        self.__serial_port = com
        self.__baud_rate = baud_rate.value

    def open(self):
        try:
            self.__ser = serial.Serial(port=self.__serial_port, baudrate=self.__baud_rate, bytesize=serial.EIGHTBITS,
                                       stopbits=serial.STOPBITS_ONE, parity=serial.PARITY_NONE, rtscts=True)
            self.__ser.write(b'RMTS,1\r')
            return self.__ser.read_until(b'\r').decode('utf-8')
        except Exception as e:
            print(e)

    def is_open(self):
        try:
            return self.__ser.is_open
        except Exception as e:
            print(e)

    def close(self):
        try:
            self.__ser.write(b'RMTS,0\r')
            return self.__ser.read_until(b'\r').decode('utf-8')
        except Exception as e:
            print(e)

    def measure_data(self):
        try:
            self.__ser.write(b'MEAS,1\r')
            result = self.__ser.read_until(b'\r').decode('utf-8')

            if result.startswith('OK00'):
                result = result.split(',')[1].split('\r')[0]
                print('Measurement will takes %s seconds.' % result)
            else:
                return result

            if self.__ser.read_until(b'\r') == b'OK00\r':
                print('Measurement is done')
                return True

        except Exception as e:
            print(e)

    def read_measured_data(self, data_mode=DataMode.COLORIMETRIC_DATA,
                           colorimetric_data_type=ColorimetricDataType.XYZ,
                           spectral_data_type=SpectralDataType.from380to479nm):
        try:
            measure_result = []
            if data_mode == DataMode.SPECTRAL_DATA:
                command = 'MEDR,' + data_mode.value + ',1,' + spectral_data_type.value + '\r'
            elif data_mode == DataMode.COLORIMETRIC_DATA:
                command = 'MEDR,' + data_mode.value + ',1,' + colorimetric_data_type.value + '\r'
            self.__ser.write(command.encode('utf-8'))
            result = self.__ser.read_until(b'\r').decode('utf-8').replace('\r', '').split(',')[1:]
            for i in range(len(result)):
                measure_result.append(struct.unpack('>f', bytes.fromhex(result[i]))[0])
            return measure_result

        except Exception as e:
            print(e)

    def measure_XYZ(self):
        self.measure_data()
        return self.read_measured_data(data_mode=DataMode.COLORIMETRIC_DATA,
                                       colorimetric_data_type=ColorimetricDataType.XYZ)


def main():
    com_port = list_all_serial_ports()[2]
    print(com_port)
    baud_rates = BaudRate.RATE_115200

    cs2000 = CS2000(com_port, baud_rates)
    cs2000.open()

    if cs2000.is_open():
        if cs2000.measure_data():
            print(cs2000.read_measured_data(data_mode=DataMode.COLORIMETRIC_DATA,
                                            colorimetric_data_type=ColorimetricDataType.XYZ))
            print(cs2000.read_measured_data(data_mode=DataMode.COLORIMETRIC_DATA,
                                            colorimetric_data_type=ColorimetricDataType.uvL))
            print(cs2000.read_measured_data(data_mode=DataMode.SPECTRAL_DATA,
                                            spectral_data_type=SpectralDataType.from380to479nm))
            print(cs2000.read_measured_data(data_mode=DataMode.SPECTRAL_DATA,
                                            spectral_data_type=SpectralDataType.from480to579nm))
            print(cs2000.read_measured_data(data_mode=DataMode.SPECTRAL_DATA,
                                            spectral_data_type=SpectralDataType.from580to679nm))
            print(cs2000.read_measured_data(data_mode=DataMode.SPECTRAL_DATA,
                                            spectral_data_type=SpectralDataType.from680to780nm))

    cs2000.close()
    print(cs2000.is_open())


if __name__ == '__main__':
    main()
