#!/usr/bin/python
# -*- coding: UTF-8 -*-
'''
Created on 2019-3-20

@author: pengjh
'''

import configparser
import time
import logging
import serial
import threading
import struct
import traceback
import sys
import serial.tools.list_ports
import platform

class OptLightController(object):
    '''
    classdocs
    '''
    
    def __init__(self,port,baudrate=9600,bytesize = 8,parity = 'N',stopbits = 1,timeout=0.1):
        self.master = serial.Serial(port,baudrate, bytesize,  parity, stopbits, timeout)
        self.lock = threading.Lock()
    def close(self):
        try:
            self.master.close()
        except Exception as e:
            raise
    def checkConnect(self,index=0):
        try:
            if self.getBrightness(1)>=0:
                return True
            else:
                return False
        except Exception as e:
            print (e)
            return False

    def commandExec(self,command):
        try:
            if self.master.isOpen() == False:
                raise Exception("opt brightness open failsss")
            self.master.flushInput()
            self.master.write(command)
            data = self.master.read(1000)
            while True:
                n=self.master.inWaiting()
                if(n==0):
                    break
                data=data+self.master.read(n)
            return data
        except Exception as e:
            raise  e

    def setStillOn(self):
        try:
            self.lock.acquire()
            command = "FF 01 01 FF 00 "
            ret = self.commandExec(command)
            self.lock.release()
            if ret=="H":
                return True
            return False
        except Exception as e:
            self.lock.release()
            raise

    def setStillOff(self):
        try:
            self.lock.acquire()
            command = "FF 01 01 FF 00"
            ret = self.commandExec(command)
            self.lock.release()
            if ret=="L":
                return True
            return False
        except Exception as e:
            self.lock.release()
            errorMsg =traceback.format_exc()
            print (errorMsg)
            raise
        
    """    
    parameter：
        channel:1-10
        value:0/1
            "0：读取常用亮度值
            1：读取备用亮度值"
    """
    def getBrightness(self,channel):
        try:
            self.lock.acquire()
            command = struct.pack('6B', 0xFF, 0x11, channel, 0x00, 0x00, 0x00)
            data = self.commandExec(command)
            data = struct.unpack("6B", data)[4]
            self.lock.release()
            return data
        except Exception as e:
            self.close()
            errorMsg =traceback.format_exc()
            print (errorMsg)
            raise e

        
    """
    parameter：
        channel:1-10
        value:0-FF
    """
    def setBrightness(self,channel,value):
        print ("set opt brightness channel:{0} and value:{1}".format(channel,value))
        try:
            self.lock.acquire()
            if value > 255:
                value = 255
            elif value < 0:
                value = 0
            command = struct.pack('6B',0xFF,0x01,channel,0x00,value,0x00)
            data = self.commandExec(command)
            data = struct.unpack('2B',data)[1]
            self.lock.release()
            return True
        except Exception as e:
            self.close()
            errorMsg =traceback.format_exc()
            print (errorMsg)
            raise e
    
    """
    parameter：
        channel:1-10
        value:1-100（以10mA为单位）
    """
    def setElectric(self,channel,value):
        try:
            self.lock.acquire()
            if value > 100:
                value = 100
            elif value < 0:
                value = 0
            command = "FF 04 %0.2x %x 00"%(channel,value)
            data = self.commandExec(command)
            self.lock.release()
            return True
        except Exception as e:
            self.lock.release()
            errorMsg =traceback.format_exc()
            print (errorMsg)
            raise
    
    """
    parameter：
        channel:1-10
        value:0/1/2（以10mA为单位）
            "0：读取手动设置电流值
            1：读取电流值
            2：读取电压值"
    """
    def getElectric(self,channel = 1,value=1):
        try:
            self.lock.acquire()
            if sys.version_info >= (3, 0):
                command = ("FF 14 %0.2x %x 00"%(channel,value)).encode("ascii")
            else:
                command = "FF 14 %0.2x %x 00"%(channel,value)
            data = self.commandExec(command)
            if sys.version_info >= (3, 0):
                data = data.decode("utf-8")
            if isinstance(int(data[1:]),int):
                self.lock.release()
                return data[1:]
            else:
                self.lock.release()
                return -1
            self.lock.release()
        except Exception as e:
            self.lock.release()
            raise
        

    def getID(self):
        try:
            self.lock.acquire()
            command = "FF 17 %0.2x %x 00"%(100,100)
            data = self.commandExec(command)
            self.lock.release()
            return True
        except Exception as e:
            self.lock.release()
            raise
if __name__ == '__main__':
    #port_list = list(serial.tools.list_ports.comports())
    #port_list = [port[0] for port in port_list]
    #print (list(port_list))

    # from CosmeticVisionInterface import CosmeticVisionInterface
    # cos_innorev = CosmeticVisionInterface()
    # cos_innorev.opt_light_col.setBrightness(0,100)
    cpl_1 = OptLightController('/dev/ttyS0')
    print (cpl_1.checkConnect())
    # cpl_2 = OptLightController('/dev/ttyS1')
    # print (cpl_2.checkConnect())
    print (cpl_1.setBrightness(0, 100))
    # for ch in range(1):
    #     for tv in ['6','8']:
    #         print cpl_1.setBrightness(0, 0)
    #         cpl_1.setBrightness(ch, 255)    #         time.sleep(1)
    #         filename = r'C:\Users\pc\Pictures\2000_01_02\ring_ch%d_tv%s.jpg' % (ch, tv)
    #         cos_innorev.capture_image(av='8', tv=tv, filename=filename)
    #
    # print cpl_2.setBrightness(0, 255)
    # print cpl_2.getBrightness(1)
    #
    #print (cpl_1.setBrightness(0, 100))
    # print(cpl_2.setBrightness(0, 0))
    # print cpl_1.setBrightness(1, 255)
    # print cpl_1.setBrightness(2, 255)
    # print cpl_1.setBrightness(3, 200)
    # print cpl_1.setBrightness(4, 200)
    # print cpl_1.setBrightness(5, 200)
    # print cpl_1.setBrightness(6, 200)




    #
    # print cpl_1.getBrightness(1)

    # print cpl_2.setBrightness(0, 0)
    # print cpl_2.getBrightness(1)
