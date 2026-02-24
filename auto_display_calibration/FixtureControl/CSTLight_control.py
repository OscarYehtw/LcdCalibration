#!/usr/bin/env python
# encoding: utf-8
'''
@author: huangxl
@contact: huangxl@innorev.com.cn
@software: garner
@file: computer_port.py
@time: 2021/12/24 17:46
@desc:
'''

import time
import serial
from threading import Lock

import serial.tools.list_ports


class computer_port(list):
    """
    获取电脑端口
    """
    _instance = None
    def __new__(cls, *args, **kw):
        if not cls._instance:
            cls._instance = super(computer_port, cls).__new__(cls, *args, **kw)
        return cls._instance

    def __init__(self,*args):
        super(computer_port, self).__init__()
        self._port_id_ = ["COM","USB"] + list(args)
        self._port_ = []
        self._refresh_port_()

    def __call__(self, *args):
        """
        获取电脑端口号
        """
        port_list = list(serial.tools.list_ports.comports())
        for each_port in port_list:
            ju_list = [port_id in each_port[0] for port_id in args]
            if True in ju_list:
                if each_port[0] not in self._port_:
                    self._add_port_(each_port[0])

    def _refresh_port_(self):
        """
        获取电脑端口号
        """
        self.clear()
        port_list = list(serial.tools.list_ports.comports())
        for each_port in port_list:
            ju_list = [port_id in each_port[0] for port_id in self._port_id_]
            if True in ju_list:
                if each_port[0] not in self._port_:
                    self._add_port_(each_port[0])

    def _add_port_(self,value):
        """
        增加端口
        :return:
        """
        self.append(value)
        self._port_.append(value)

    def use_port(self,*args):
        """ 使用端口 """
        for _args in args:
            self.remove(_args)
        return self.__repr__()

    def computer_port(self):
        """ 返回电脑的所有端口 """
        return self._port_



class CSTLight(object):
    """docstring for Loadcell_232_ L100-B """

    def __init__(self,port=None, baudrate=19200, parity="N", stopbits=1, bytesize=8, timeout=0.15):
        self.tglock = Lock()
        self.port, self.baudrate, self.bytesize, self.parity, self.stopbits, self.timeout = port, baudrate, bytesize, parity, stopbits, timeout
        self.master = None
        self._decimal_number_ = False



    def checkConnect(self,timeout=1):
        """
        :return:
        """
        try:
            s  = time.time()
            self.master = serial.Serial(self.port, self.baudrate, self.bytesize, self.parity, self.stopbits,
                                        self.timeout)
            while  time.time() - s < timeout:
                print(self.write("T#"))
                if self.write("T#") == "H":
                    return True
            return False
        except Exception as e:
            return False



    def set_Brightness(self,chanel,value):
        """
        :param chanel:
        :param value:
        :return:
        """
        if not isinstance(chanel,int) or not isinstance(value,int):
            raise Exception("input chanel or value Erorr  chanel or value not in int")
        if value > 255:
            value = 255
        if value <0:
            value =0
        chanel = str(chanel).replace("1","A").replace("2","B")
        value = f"{value}"
        while len(value) < 4:
            value = "0"+value
        comd = f"S{chanel}{value}#"
        data = self.write(comd)
        return ("a" in data) or ("b" in data)



    def get_Brightness(self,chanel=0):
        return_data = {}
        if chanel == 0:
            return_data[1] = int(self.write("SA#").replace("a",""))
            return_data[2] = int(self.write("SB#").replace("b",""))
            return return_data
        else:
            command = f"S{chanel}#".replace("1","A").replace("2","B")
            return int(self.write(command).replace("a", "").replace("b", ""))



    def write(self, command, timeout=0.5, cmdsleeptime=0.05):
        """ write command """
        with self.tglock:
            self.master.write(command.encode("ascii"))
            time.sleep(cmdsleeptime)
            num = False
            st = time.time()
            while time.time() - st < timeout:
                if num:
                    data = self.master.read(num).decode("utf-8")
                    return data
                else:
                    num = self.master.inWaiting()
            return False

if __name__ == "__main__":
    a = CSTLight("/dev/ttyS0")
    print(a.checkConnect(),"====================")
    print(a.set_Brightness(1,0))
    print((a.get_Brightness()))
    # print(a.read("T#"))




