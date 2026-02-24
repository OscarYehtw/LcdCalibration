#!/usr/bin/python
# -*- coding: UTF-8 -*-
'''
Created on 2017-09-03

@author: zhouql
'''
import time
import serial
import pdb
#from innorev.Controller import Serials
from threading import  Lock
class InnorevController(object):
    '''
    classdocs
    '''
    def __init__(self,port,
        baudrate=115200,
        parity = serial.PARITY_NONE,
        stopbits = serial.STOPBITS_ONE,
        bytesize = serial.EIGHTBITS,
        timeout=0.02,parent=None):
        self.__Lock__ =  Lock()
        self.master = serial.Serial(port,baudrate, bytesize,  parity, stopbits, timeout)
        self.port = port
        self.baudrate=baudrate
        self.parity=parity
        self.stopbits=stopbits
        self.bytesize=bytesize
        self.timeout=timeout


    def getPort(self):
        return self.port
    def close(self):
        self.master.close()
    def reconnect(self):
        self.close()
        ports = getSerials()
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

    def checkConnect(self,slave=0):
        """
           check the serial port is or not innorev board serial port
            @param slave: default,not used.just adapt style
            @return: bool:success True,failed False
        """
        # self.WriteSN(1)
        ok,data = self.readDI()
        ok,data = self.readDI()
        if ok:
            return True
        else:
            return False


    def WriteID(self,value,timeout=1):
        """
            @param value: innorev board id
            @param timeout: wait timeout.
            @return: tuple(bool,str)
                    0:success True,failed False
                    1:source data
        """
        if self.master.isOpen() :
            self.master.flushInput()
            command = b"WriteEEPROM 0x0090 %#.2x\r"%(value)
            n=self.master.write(command)
            data = self.master.readlines()
            self.master.flushOutput()
            if len(data)>=5 and data[3].strip()==b"OK":
                return True,data[2].strip()
            else:
                 return False,data

    def WriteSN(self,value,timeout=1):
        """
            @param value: innorev board id
            @param timeout: wait timeout.
            @return: tuple(bool,str)
                    0:success True,failed False
                    1:source data
        """
        if self.master.isOpen() :
            self.master.flushInput()
            command = b"WriteSN %.4d\r"%(value)
            n=self.master.write(command)
            data = self.master.readlines()
            self.master.flushOutput()
            if len(data)>=4 and data[2].strip()==b"OK":
                return True,data[1].strip()
            else:
                return False,data
       
    def analysisResultDI(self,result,index):
        """
            @param value: innorev board id
            @param timeout: wait timeout.
            @return: tuple(bool,str)
                    0:success True,failed False
                    1:source data
        """
        num=-1
        binary = bin(int(result,16))
        if len(binary)==34:
            if index>=24:
                num = (int(str(result),16)>>index-24+4-1)&1
            else:
                num = (int(str(result),16)>>index+8-1)&1
        else:
            num = (int(result,16)>>index-1)&1
        return num


    def readSingle(self,index,inputType=0):
        """
        @param index 1~20
              inputType 1 output,0 input
        @return num, io status. 0 is on,1 is off
                data,source data
        """
        if inputType:
            num = -1
            ok,data = self.readDO()
            while not ok or not data:
                ok,data = self.readDO()
            return (int(data,16)>>index-1)&1,data
        else:
            ok,data = self.readDI()
            while not ok or not data:
                ok,data = self.readDI()
            num = self.analysisResultDI(data,index)
            return num,data


    def ReadID(self,timeout=1):
        """
        @param timeout wait for time
        @return tuple(bool, str)
                0:success True,failed False
                1:success it is board id,like "1",failed,it is source data or errormessage
                source data: like "readEEprom 0x0090\n \n0x01\nOK\n >"
        """
        if self.master.isOpen() :
            self.master.flushInput()
            command = b"readEEprom 0x0090\r"
            #pdb.set_trace()
            n=self.master.write(command)
            data = self.master.readlines()
            self.master.flushOutput()
            if len(data)>=4 and data[2].strip()=="OK":
                return True,data[1].strip()
            else:
                return False,data

    def ReadSN(self,timeout=1):
        """
        @param timeout wait for time
        @return tuple(bool, str)
                0:success True,failed False
                1:success it is board id,like "1",failed,it is source data or errormessage
                source data: like "readEEprom 0x0090\n \n0x01\nOK\n >"
        """
        if self.master.isOpen() :
            self.master.flushInput()
            command = b"readsn\r"
            #pdb.set_trace()
            n=self.master.write(command)
            data = self.master.readlines()
            self.master.flushOutput()
            if len(data)>=4 and data[2].strip()==b"OK":
                return True,data[1].strip()[0:4]
            else:
                return False,data



    def readDI(self,timeout=1,retry=5):
        """
        @param timeout wait for time
        @return tuple(bool, str)
                0:success True,failed False
                1:success: like "0xfffe",failed,it is source dataor error message
                source data: like "ReadDI\n\nNAK\n>"
        """
        if self.master.isOpen() :
            self.master.flushInput()
            command = b"ReadDI\r"
            self.master.flushInput()
            self.master.write(command)
            data = self.master.readlines()
            self.master.flushOutput()
            if len(data)>=5 and data[3].strip()==b"OK":
                return True,data[2].strip()
            else:
                return False,data



    def readDO(self,timeout=1):
        """
        @param timeout wait for time
        @return tuple(bool, str)
                0:success True,failed False
                1:success: like "0xfffe",failed,it is source data or error message
                source data: like "ReadDO\n\nNAK\n>" "ReadDO\n\n0xfffe\n>"
        """
        if self.master.isOpen() :
            command=b"ReadDO\r"
            self.master.flushInput()
            n=self.master.write(command)
            self.master.flushOutput()
            data = self.master.readlines()
            if len(data)>=5 and data[3].strip()==b"OK":
                return True,data[2].strip()
            else:
                return False,data



    def writeDO(self,index,status,timeout=1):
        """
        @param index for IO Mapping.the value is 1~16
        @param timeout wait for time
        @return tuple(bool, str)
                0:success True,failed False
                1:success: like "0xfffe",failed,it is source data or error message
                source data: like "ReadDO\n\nNAK\n>" or "ReadDO\n\n0xfffe\n>"
        """
        if self.master.isOpen():
            command = b"WriteDO %#.2x %#.2x\r"%(index,status)
            self.master.flushInput()
            self.master.write(command)
            data = self.master.readlines()
            self.master.flushOutput()
            if len(data)>=4 and data[2].strip()==b"OK":
                return True,data
            else:
                return False,data

if __name__ == '__main__':
    control = InnorevController("/dev/ttyS0")
    print (control.writeDO(10,0))
    # print(control.writeDO(11,1))
    print(control.readSingle(9))
    
