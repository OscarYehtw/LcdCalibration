#!/usr/bin/python
# -*- coding: UTF-8 -*-
'''
Created on 2017-09-03

@author: zhouql
'''

import time
import serial
# from innorev.Controller import class_func_check,getSerials
import functools
import io
import traceback
import threading
def class_func_check(arg_of_decorator):
    def deco(func):
        @functools.wraps(func)
        def wrapper(self, *arg, **kw):
            for i in range(arg_of_decorator):
                flag = False
                # if not isinstance(self, object):
                #     raise TypeError("class_func_check must be used in class function")
                if not hasattr(self, "lock"):
                    self.lock = threading.RLock()
                # if not hasattr(self, "logger"):
                #     self.logger = create_logger(self.__class__.__name__)
                try:
                    with self.lock:
                        starttime = time.time()
                        flag = func(self, *arg, **kw)
                        if hasattr(self, "turnoff_light_signal_red"):
                            pass  # self.turnoff_light_signal_red()
                        # self.logger.info("call %s finish,times is:%f" % (func.__name__, time.time() - starttime))
                        return flag
                except:
                    fp = io.StringIO()
                    traceback.print_exc(file=fp)
                    msg = fp.getvalue()
                    # self.logger.error(str(msg) + " retry num = %d" % i)
                    # if i == arg_of_decorator - 1:
                    #     if hasattr(self, "turnoff_light_signal_green"):
                    #         self.turnoff_light_signal_green()
                    #     return flag
                    # if hasattr(self, "turnon_light_signal_red"):
                    #     self.turnon_light_signal_red()
                    continue

        wrapper.__name__ = func.__name__
        return wrapper

    return deco

class CPLController(object):
    '''
    classdocs
    '''
    
    CHANNELS = [b"A",b"B",b"C",b"D",b"E",b"F"]
    def __init__(self,port,baudrate=19200,bytesize = 8,parity = 'N',stopbits = 1,timeout=0.1):
        self.port = port
        self.master = serial.Serial(port,baudrate, bytesize,  parity, stopbits, timeout)
        self.port = port
        self.baudrate=baudrate
        self.parity=parity
        self.stopbits=stopbits
        self.bytesize=bytesize
        self.timeout=timeout
    def reconnect(self):
        self.close()
        ports = ['ttyS0', 'ttyS1']
        for port in ports:
            self.master = serial.Serial(port,self.baudrate, self.bytesize,  self.parity, self.stopbits, self.timeout)
            if self.checkConnect():
                self.port=port
                break
            else:
                self.master.close()
                self.master=None
        if not self.master:
            return None
    @class_func_check(1)
    def close(self):
        self.master.close()

    @class_func_check(1)
    def checkConnect(self,index=0):
        value = self.getBrightness(0)
        if isinstance(value,bool):
            return value
        return -1!=value

    def getPort(self):
        return self.port
    def commandExec(self,command):
        self.master.flushInput()
        self.master.write(command)
        data = self.master.read(1000)
        while True:
            n=self.master.inWaiting()
            if(n==0):
                break
            data=data+self.master.read(n)
        self.master.flushOutput()
        return data
    @class_func_check(3)
    def setStillOn(self):
        command = b"SH1111#"
        ret = self.commandExec(command)
        if ret==b"H":
            return True
        return False
      
    @class_func_check(3)
    def setStillOff(self):
        command = b"SL000#"
        ret = self.commandExec(command)
        if ret==b"L":
            return True
        return False
       

    @class_func_check(3)
    def getBrightness(self,channel):
        command = b"S%s#"%(self.CHANNELS[channel])
        data = self.commandExec(command)
        # data = data.decode('utf-8')
        if isinstance(int(data[1:]),int) and self.CHANNELS[channel].lower()==data[0:1]:
            return data[1:].decode('utf-8')
        else:
            return -1
    @class_func_check(3)
    def setBrightness(self,channel,value):
        command = b"S%s%0.4d#"%(self.CHANNELS[channel],value)
        data = self.commandExec(command)
        if data.strip().upper()==self.CHANNELS[channel]:
            return True
        else:
            return False

    @class_func_check(3)
    def setElectric(self,index,value):
        command = b"SI%s%0.3d#"%(index+1,value)
        data = self.commandExec(command)
        return True
       
if __name__=="__main__":
      cs = CPLController("/dev/ttyS0")
      print(cs.checkConnect())
      print(cs.getBrightness(1))
      
