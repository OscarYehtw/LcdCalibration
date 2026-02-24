#!/usr/bin/python
# -*- coding: UTF-8 -*-
'''
Created on 2018-05-13 by LiaoLB

'''
import sys
import time
import serial
import serial.tools.list_ports
import threading

''' 2020/12/03 update from lzq
1.Update cl200a to read 0 lux Evxy exception..
'''

class CL200AController(object):
    '''
    classdocs
    '''

    def __init__(self, port,
                 baudrate=9600,
                 parity=serial.PARITY_EVEN,
                 stopbits=serial.STOPBITS_ONE,
                 bytesize=serial.SEVENBITS,
                 timeout=0.1, parent=None):
        self.master = serial.Serial(port, baudrate, bytesize, parity, stopbits, timeout)
        self.lock = threading.Lock()

    def get_Serial_ports(self):
        sp_list = list(serial.tools.list_ports.comports())
        lists = list()
        for port in sp_list:
            port = str(port.device)
            if ("USB" in port):
                lists.append(port)
        return lists

    def close(self):
        self.master.close()

    def checkConnect(self, index=0):
        try:
            if self.setModelPc():
                return True
            else:
                return False
        except Exception as e:
            print("Exception%s" % (e))
            return False,

    def read(self):
        try:
            data = None
            self.lock.acquire()
            if self.master.isOpen():
                self.master.flushInput()
                command1 = '\x02'.encode() + ('994011  ').encode('ascii') + '\x03'.encode() + ('07').encode(
                    'ascii') + '\x0D'.encode() + '\x0A'.encode()
                sys.stdout.flush()
                n = self.master.write(command1)
                time.sleep(0.3)
                command2 = '\x02'.encode() + ('994021  ').encode('ascii') + '\x03'.encode() + ('04').encode(
                    'ascii') + '\x0D'.encode() + '\x0A'.encode()
                sys.stdout.flush()
                n = self.master.write(command2)
                time.sleep(0.3)
                sys.stdout.flush()
                n = self.master.write(command2)
                time.sleep(0.3)
                sys.stdout.flush()
                n = self.master.write(command2)
                time.sleep(0.3)
                command3 = '\x02'.encode() + ('00081200').encode('ascii') + '\x03'.encode() + ('08').encode(
                    'ascii') + '\x0D'.encode() + '\x0A'.encode()
                sys.stdout.flush()
                n = self.master.write(command3)
                self.master.flushOutput()
                data = self.master.read(1000)
                while True:
                    n = self.master.inWaiting()
                    if (n == 0):
                        break
                    data = data + self.master.read(n)
                    self.master.flushOutput()
                data = data.decode('utf-8')
                print("------------", data)
                delta_uv_value = None

                if ("=" in data):
                    self.lock.release()
                    return True, 0, 0, 0
                if len(data) != 32 or "----" in data:
                    self.lock.release()
                    return False, 0, 0, 0
                if ("+" in data):  # judge “+” is or not in data
                    color_temperature = data[16:20]
                    integer_digit = data[14]
                    delta_uv = data[22:27]
                    delta_uv_digit = data[21]
                    if "-" in delta_uv_digit:
                        delta_uv_value = -(int(delta_uv[0:4]) * self.exponent(delta_uv[-1]))
                    elif "=" in delta_uv_digit:
                        delta_uv_value = 0
                    elif "+" in delta_uv_digit:
                        delta_uv_value = (int(delta_uv[0:4]) * self.exponent(delta_uv[-1]))
                    else:
                        uv_value = "no value"
                    if (integer_digit == "3"):
                        luxmeter = data[10:13].strip() + "." + data[13]
                        self.lock.release()
                        return True, float(luxmeter), float(color_temperature), delta_uv_value
                    elif (integer_digit == "4"):
                        luxmeter = data[10:14].strip()
                        self.lock.release()
                        return True, float(luxmeter), float(color_temperature), delta_uv_value
                    elif (integer_digit == "5"):
                        luxmeter = data[10:14] + "0"
                        self.lock.release()
                        return True, float(luxmeter), float(color_temperature), delta_uv_value
                else:
                    self.lock.release()
                    return False, "no return value", "no return value", "no return value"
            else:
                self.lock.release()
                return False, "no return value", "no return value", "no return value"
        except Exception as e:
            print(str(e))
            self.lock.release()
            return False, str(e), "no return value", "no return value", "no return value"

    def read_XYZ(self):
        x = 0
        y = 0
        z = 0
        try:
            data = None
            self.lock.acquire()
            if self.master.isOpen():
                self.master.flushInput()
                command1 = '\x02'.encode() + ('994011  ').encode('ascii') + '\x03'.encode() + ('07').encode(
                    'ascii') + '\x0D'.encode() + '\x0A'.encode()
                sys.stdout.flush()
                n = self.master.write(command1)
                time.sleep(0.1)
                command2 = '\x02'.encode() + ('994021  ').encode('ascii') + '\x03'.encode() + ('04').encode(
                    'ascii') + '\x0D'.encode() + '\x0A'.encode()
                sys.stdout.flush()
                n = self.master.write(command2)
                time.sleep(0.1)
                sys.stdout.flush()
                n = self.master.write(command2)
                time.sleep(0.1)
                sys.stdout.flush()
                n = self.master.write(command2)
                time.sleep(0.1)
                command3 = '\x02'.encode() + ('00011200').encode('ascii') + '\x03'.encode() + ('01').encode(
                    'ascii') + '\x0D'.encode() + '\x0A'.encode()
                sys.stdout.flush()
                n = self.master.write(command3)
                self.master.flushOutput()
                data = self.master.read(1000)
                while True:
                    n = self.master.inWaiting()
                    if (n == 0):
                        break
                    data = data + self.master.read(n)
                    self.master.flushOutput()
                data = data.decode('utf-8')
                if ("+" in data):  # judge “+” is or not in data
                    data_list = data.split("+")
                    for index in range(1, len(data_list)):
                        value = data_list[index][0:5]
                        #                     color_temperature = data[16:20]
                        integer_digit = value[-1]
                        # print value
                        if (integer_digit == "3"):
                            if index == 1:
                                x = value[0:3].strip() + "." + value[3]
                            elif index == 2:
                                y = value[0:3].strip() + "." + value[3]
                            elif index == 3:
                                z = value[0:3].strip() + "." + value[3]
                        #                             self.lock.release()
                        #                             return True,luxmeter,color_temperature
                        elif (integer_digit == "4"):
                            if index == 1:
                                x = value[0:4].strip()
                            elif index == 2:
                                y = value[0:4].strip()
                            elif index == 3:
                                z = value[0:4].strip()
                        #                             self.lock.release()
                        #                             return True,luxmeter,color_temperature
                        elif (integer_digit == "5"):
                            if index == 1:
                                x = value[0:4] + "0"
                            elif index == 2:
                                y = value[0:4] + "0"
                            elif index == 3:
                                z = value[0:4] + "0"
                self.lock.release()
                return True, float(x), float(y), float(z)
            else:
                self.lock.release()
                return False, float(x), float(y), float(z)
        except Exception as e:
            print(str(e))
            self.lock.release()
            return False, str(e)

    def read_Evxy(self):
        try:
            data = None
            self.lock.acquire()
            if self.master.isOpen():
                self.master.flushInput()
                command1 = '\x02'.encode() + ('994011  ').encode('ascii') + '\x03'.encode() + ('07').encode(
                    'ascii') + '\x0D'.encode() + '\x0A'.encode()
                sys.stdout.flush()
                n = self.master.write(command1)
                time.sleep(0.1)
                command2 = '\x02'.encode() + ('994021  ').encode('ascii') + '\x03'.encode() + ('04').encode(
                    'ascii') + '\x0D'.encode() + '\x0A'.encode()
                sys.stdout.flush()
                n = self.master.write(command2)
                time.sleep(0.1)
                sys.stdout.flush()
                n = self.master.write(command2)
                time.sleep(0.1)
                sys.stdout.flush()
                n = self.master.write(command2)
                time.sleep(0.1)
                command3 = '\x02'.encode() + ('00021200').encode('ascii') + '\x03'.encode() + ('02').encode(
                    'ascii') + '\x0D'.encode() + '\x0A'.encode()
                sys.stdout.flush()
                n = self.master.write(command3)
                self.master.flushOutput()
                data = self.master.read(1000)
                while True:
                    n = self.master.inWaiting()
                    if (n == 0):
                        break
                    data = data + self.master.read(n)
                    self.master.flushOutput()
                # print "--------------------",data
                data = data.decode('utf-8')
                Ev_x_y = []
                if ("+" in data):  # judge “+” is or not in data
                    data_list = data.split("+")
                    for index in range(1, len(data_list)):
                        value = data_list[index][0:5]
                        #                     color_temperature = data[16:20]
                        integer_digit = value[-1]
                        data_Ev = int(value[0:-1]) * self.exponent(int(integer_digit))
                        # print "---------",data_Ev
                        Ev_x_y.append(float(data_Ev))
                        # print value
                        # if (integer_digit == "3"):
                        #     if index == 1:
                        #         x = value[0:3].strip() + "." + value[3]
                        #     elif index == 2:
                        #         y = value[0:3].strip() + "." + value[3]
                        #     elif index == 3:
                        #         z = value[0:3].strip() + "." + value[3]
                        # #                             self.lock.release()
                        # #                             return True,luxmeter,color_temperature
                        # elif (integer_digit == "4"):
                        #     if index == 1:
                        #         x = value[0:4].strip()
                        #     elif index == 2:
                        #         y = value[0:4].strip()
                        #     elif index == 3:
                        #         z = value[0:4].strip()
                        # #                             self.lock.release()
                        # #                             return True,luxmeter,color_temperature
                        # elif (integer_digit == "5"):
                        #     if index == 1:
                        #         x = value[0:4] + "0"
                        #     elif index == 2:
                        #         y = value[0:4] + "0"
                        #     elif index == 3:
                        #         z = value[0:4] + "0"
                    self.lock.release()
                    return True, round(Ev_x_y[0], 4), round(Ev_x_y[1], 4), round(Ev_x_y[2], 4)
                else:
                    return True, 0, 0, 0
            else:
                self.lock.release()
                return False, 0, 0, 0
        except Exception as e:
            # print(str(e))
            # self.lock.release()
            return False, 0, 0, 0

    def setModelPc(self):
        try:
            self.lock.acquire()
            if self.master.isOpen():
                self.master.flushInput()
                command = '\x02'.encode() + ('00541   ').encode('ascii') + '\x03'.encode() + ('13').encode(
                    'ascii') + '\x0D'.encode() + '\x0A'.encode()
                self.master.write(command)
                data = self.master.read(1000)
                while True:
                    n = self.master.inWaiting()
                    if (n == 0):
                        break
                    data = data + self.master.read(n)
                self.lock.release()
                return data
            self.lock.release()
        except Exception as e:
            self.lock.release()
            return False, "Exception:%s" % (str(e))

    def quit_PC_mode(self):
        try:
            self.lock.acquire()
            if self.master.isOpen():
                self.master.flushInput()
                command = '\x02'.encode() + ('00540   ').encode('ascii') + '\x03'.encode() + ('12').encode(
                    'ascii') + '\x0D'.encode() + '\x0A'.encode()
                self.master.write(command)
                data = self.master.read(1000)
                while True:
                    n = self.master.inWaiting()
                    if (n == 0):
                        break
                    data = data + self.master.read(n)
                self.lock.release()
                return data
            self.lock.release()
        except Exception as e:
            self.lock.release()
            return False, "Exception:%s" % (str(e))

    def exponent(self, value):
        if int(value) == 0:
            return 10 ** (-4)
        elif int(value) == 1:
            return 10 ** (-3)
        elif int(value) == 2:
            return 10 ** (-2)
        elif int(value) == 3:
            return 10 ** (-1)
        elif int(value) == 4:
            return 10 ** (0)
        elif int(value) == 5:
            return 10 ** (1)
        elif int(value) == 6:
            return 10 ** (2)
        elif int(value) == 7:
            return 10 ** (3)
        elif int(value) == 8:
            return 10 ** (4)
        elif int(value) == 9:
            return 10 ** (5)


if __name__ == "__main__":
    # def connect():
    con = CL200AController("/dev/ttyUSB4")
    print(con.checkConnect())
    # con.get_Serial_ports()
    con.setModelPc()
    print(con.read())
    print(con.read_Evxy())
    # print (con.read_XYZ())
    # print con.setread_EvxyModelPc()

    # while True:
    #     print con.read()
    #     # print con.read_Evxy()
    #     # print con.read_XYZ()
    # con.quit_PC_mode()

#     str = "00011 20+35543+38663+3644300"
#     data_list = str.split("+")
#     print data_list
