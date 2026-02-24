#!/usr/bin/python
# -*- coding: UTF-8 -*-
'''
Created on 2018-08-28

@author: liaolb

'''
import time
import serial
import threading
import sys

class Innorev_Light_Cotrol(object):

    Channels = [b"0", b"1", b"2", b"3", b"4", b"5", b"6", b"7",  b"8",  b"9"]

    def __init__(self,port,baudrate=115200,bytesize = 8,parity = 'N',stopbits = 1,timeout=0.1):
        self.port = port
        self.master = serial.Serial(port,baudrate, bytesize,  parity, stopbits, timeout)
        self.lock = threading.Lock()

    def close(self):
        try:
            if self.master.is_open():
                self.master.close()
        except Exception as e:
            print(str(e))
        finally:
            pass

    def checkConnect(self):
        try:
            flag,_result = self.ReadSN()
            flag,_result = self.ReadSN()
            print(flag,_result)
            if(_result):
                return True
            else:
                return False
        except Exception as e:
            # print "==Connect fail==",str(e)
            return False

    def commandExec(self,command):
        try:
            self.master.flushInput()
            # if sys.version_info >= (3, 0):
            #     command = command.encode("ascii")
            self.master.write(command)
            time.sleep(0.1)
            ret = self.master.readlines()
            if 'nak' in ret:
                self.master.flushInput()
                self.master.write(command)
                time.sleep(0.1)
                ret = self.master.readlines()
            # if sys.version_info >= (3, 0):
            #     ret = ret.decode("utf-8")
            return ret
        except Exception as e:
            print(str(e),"command execute error")

    def getBrightness(self, channel):
        try:
            self.lock.acquire()
            command = b"get %s\r\n" % (self.Channels[channel])
            data = self.commandExec(command)
            if isinstance(int(data[0][0:4]), int):
                value = int(data[0].strip())
                if channel == 7:
                    value = int(data[0].strip())*0.1
                return value
            else:
                return False
        except Exception as e:
            # print str(e)
            raise
        finally:
            self.lock.release()

    def setBrightness(self,channel,value):
        #value <4500
        #channel 7 brightness set duty
        # print 11111111111111111111111,channel,value


        try:
            # if channel == 2:
            #     channel = 6
            # if channel == 3:
            #     channel = 9
            #     if value == 15000:
            #         value = 0
            #     if value == 75000:
            #         value = 50
            self.lock.acquire()
            # if channel == 9:
            #     value = 1000*value/100
            command = b"set %s %0.4d\r\n"%(self.Channels[channel],value)
            data = self.commandExec(command)
            if(b"OK" in data[0]):
                return True
            else:
                return False
        except Exception as e:
            raise
        finally:
            self.lock.release()

    def setFrequency(self,frequency):
        try:
            self.lock.acquire()
            if(frequency<0 or frequency>10000):
                print("frequency out range")
                return False
            # if (channel != 7):
            #     print "channel must be 7 "
            #     return False
            command = b"set frequency %d %0.4d\r\n"%(9,frequency)
            data = self.commandExec(command)
            if(b"OK" in data[0]):
                return True
            else:
                return False
        except Exception as e:
            # print str(e)
            pass
        finally:
            self.lock.release()

    def getFrequency(self):
        try:
            self.lock.acquire()
            command = b"get frequency 9\r\n"
            data = self.commandExec(command)
            if (b"OK" in data[1]):
                return data[0][0:4]
            else:
                return False
        except Exception as e:
            # print str(e)
            pass
        finally:
            self.lock.release()

    def WriteSN(self, value):
        try:
            self.lock.acquire()
            if self.master.isOpen():
                self.master.flushInput()
                command = b"write sn %.4d\r\n" % (value)
                data = self.commandExec(command)
                if (b"OK" in data[0]):
                    return True
                else:
                    return False
        except Exception as e:
            return False, str(e)
        finally:
            self.lock.release()

    def ReadSN(self):
        try:
            self.lock.acquire()
            if self.master.isOpen():
                self.master.flushInput()
                command = b"read sn\r\n"
                self.master.flushOutput()
                data = self.commandExec(command)
                if (b"OK" in data[1]):
                    return data[0][0:4],True
                else:
                    return "null",False
        except Exception as e:
            # print "===readsn excption===%s" % str(e)
            return "null",False
        finally:
            self.lock.release()

    def turn_on(self,channel):
        try:
            self.lock.acquire()
            if self.master.isOpen():
                self.master.flushInput()
                command =b"turn on %s\r\n" %(self.Channels[channel])
                data=self.commandExec(command)
                time.sleep(0.1)
                if(b"OK" in data[0]):
                    return True
                else:
                    return False
        except Exception as e:
            # print str(e)
            return False
        finally:
            self.lock.release()

    def turn_off(self,channel):
        try:
            self.lock.acquire()
            if self.master.isOpen():
                self.master.flushInput()
                command =b"turn off %s\r\n" %(self.Channels[channel])
                data=self.commandExec(command)
                time.sleep(0.1)
                if(b"OK" in data[0]):
                    return True
                else:
                    return False
        except Exception as e:
            # print str(e)
            return False
        finally:
            self.lock.release()

    def getAD(self, channel):
        try:
            self.lock.acquire()
            print(self.Channels[channel])
            command = b"get ad %s\r\n" % (self.Channels[channel])
            data = self.commandExec(command)
            if isinstance(int(data[0][0:4]), int):
                return data[0][0:4]
            else:
                return False
        except Exception as e:
            # print str(e)
            raise
        finally:
            self.lock.release()


if __name__ == '__main__':
    light = Innorev_Light_Cotrol("/dev/ttyS9")
    print(light.checkConnect())
    light.setBrightness(1, 500)
    # for i in range(20):
    #     try:
    #
    #         light = Innorev_Light_Cotrol("/dev/ttyS%s"%i)
    #         print(light.checkConnect(), "/dev/ttyS%s"%i)
    #     except Exception as e:
    #         print(e)
    # print(light.setBrightness(4, 500))
    # print(light.setFrequency(2))
    # print(light.getAD(4))
    # print(light.setBrightness(6,0))
    # print(light.getBrightness(6))
    # light.turn_off(1)
    # print light.setBrightness(6,2000)    #设置1通道亮度为1234
    # print light.setBrightness(7,100)    #设置1通道亮度为1234
    # print light.getFrequency()           #获取当前输出PWM的频率
    # print(light.getFrequency())           #获取当前输出PWM的频率
    # print(light.setFrequency(1200))       #设置PWM输出频率为1000
    # light.setBrightness(7,100)
    # print light.ReadSN()                 #读取控制器的SN序列号
    # print light.ReadSN()                 #读取控制器的SN序列号
    # print light.WriteSN(1234)            #写控制器的SN序列号
    # print light.turn_on(1)               #打开1通道光源
    # print light.turn_off(1)              #关闭1通道光源
    # print light.getAD(2)                 #获取模拟量通道1的值
    # light.close()
    # i=0
    # while i<6:
    #     i += 1
    # for i in range(1,7):
    #     light.turn_off(i)
    # print light.getBrightness(7)
    # print light.getBrightness(6)

