#!/usr/bin/python
# -*- coding: UTF-8 -*-
'''
Created on 2017-09-03

@author: zhouql
'''
import sys
import time
import serial
import threading


class InnorevController(object):
    '''
    classdocs
    '''
    def __init__(self,port,
        baudrate=115200,
        parity = serial.PARITY_NONE,
        stopbits = serial.STOPBITS_ONE,
        bytesize = serial.EIGHTBITS,
        timeout=0.1,parent=None):
        self.master = serial.Serial(port,baudrate, bytesize,  parity, stopbits, timeout)
        self.lock = threading.Lock()
    def close(self):
        self.master.close()
    """
       check the serial port is or not innorev board serial port
        @param slave: default,not used.just adapt style
        @return: bool:success True,failed False
    """
    def checkConnect(self,slave=0):
        try:
            ok,data = self.readDI()
            if ok:
                return True
            else:
                return False
        except Exception as e:
            print("Exception%s"%(e))
            return False,
    """
        @param value: innorev board id
        @param timeout: wait timeout.
        @return: tuple(bool,str)
                0:success True,failed False
                1:source data
    """
    def WriteID(self,value,timeout=1):
        try:
            self.lock.acquire()
            if self.master.isOpen() :
                self.master.flushInput()
                if sys.version_info >= (3, 0):
                    command = ("WriteEEPROM 0x0090 %#.2x\r"%(value)).encode("ascii")
                else:
                    command = "WriteEEPROM 0x0090 %#.2x\r"%(value)
                n=self.master.write(command)
                data = self.master.read(1000)
                starttime = time.time()
                while True:
                    n=self.master.inWaiting()
                    if(n==0):
                        break
                    if time.time()-starttime>timeout:
                        break
                    data=data+self.master.read(n)
                if sys.version_info >= (3, 0):
                    data = data.decode("utf-8")
                lst = data.split("\r\n")
                if lst[2]=="OK":
                    return True,data
                else:
                    return False,data
        except Exception as e:
            return False,str(e)
        finally:
            self.lock.release()
    def WriteSN(self,value,timeout=1):
        try:
            self.lock.acquire()
            if self.master.isOpen() :
                self.master.flushInput()
                if sys.version_info >= (3, 0):
                    command = ("WriteSN %.4d\r"%(value)).encode("ascii")
                else:
                    command = "WriteSN %.4d\r"%(value)
                n=self.master.write(command)
                data = self.master.read(1000)
                starttime = time.time()
                while True:
                    n=self.master.inWaiting()
                    if(n==0):
                        break
                    if time.time()-starttime>timeout:
                        break
                    data=data+self.master.read(n)
                if sys.version_info >= (3, 0):
                    data = data.decode("utf-8")
                lst = data.split("\r\n")
                if lst[2]=="OK":
                    return True,data
                else:
                    return False,data
        except Exception as e:
            return False,str(e)
        finally:
            self.lock.release()
    def analysisResultDI(self,result,index):
        try:
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
        except Exception as e:
            return str(e)
    """
    @param index 1~20
          inputType 1 output,0 input
    @return num, io status. 0 is on,1 is off
            data,source data
    """


    def readSingle(self, index, inputType=0):
        index=int(index)
        if inputType:
            num = -1
            ok, data = self.readDO()
            if ok:
                return (int(data, 16) >> index - 1) & 1, data
        else:
            ok, data = self.readDI()
            starttime = time.time()
            while (not ok or not data) and (time.time() - starttime < 5):
                ok, data = self.readDI()
            num = self.analysisResultDI(data, index)
            return num, data
    """
    @param timeout wait for time
    @return tuple(bool, str)
            0:success True,failed False
            1:success it is board id,like "1",failed,it is source data or errormessage
            source data: like "readEEprom 0x0090\n \n0x01\nOK\n >"
    """
    def ReadID(self,timeout=1):
        try:
            self.lock.acquire()
            if self.master.isOpen() :
                self.master.flushInput()
                if sys.version_info >= (3, 0):
                    command = "readEEprom 0x0090\r".encode("ascii")
                else:
                    command = "readEEprom 0x0090\r"
                #pdb.set_trace()
                self.master.flushOutput()
                n=self.master.write(command)
                data = self.master.read(1000)
                starttime = time.time()
                while True:
                    time.sleep(0.01)
                    n=self.master.inWaiting()
                    if(n==0):
                        break
                    if time.time()-starttime>timeout:
                        break
                    data += self.master.read(n)
                if sys.version_info >= (3, 0):
                    data = data.decode("utf-8") 
                lst = data.split("\r\n")
                if len(lst)==5 and lst[3]=="OK":
                    return True,lst[2]
                else:
                    return False,data
        except Exception as e:
            print("==========readid excption=======%s\n"%str(e))
            return False,str(e),
        finally:
            self.lock.release()

    def ReadSN(self,timeout=1):
        try:
            self.lock.acquire()
            if self.master.isOpen() :
                self.master.flushInput()
                if sys.version_info >= (3, 0):
                    command = "readsn\r".encode("ascii")
                else:
                    command = "readsn\r"
                #pdb.set_trace()
                self.master.flushOutput()
                n=self.master.write(command)
                data = self.master.read(1000)
                starttime = time.time()
                while True:
                    time.sleep(0.01)
                    n=self.master.inWaiting()
                    sys.stdout.flush()
                    if(n==0):
                        break
                    if time.time()-starttime>timeout:
                        break
                    data += self.master.read(n)
                if sys.version_info >= (3, 0):
                    data = data.decode("utf-8")
                lst = data.split("\r\n")
                if (len(lst)==4 and lst[2]=="OK") or (len(lst)==5 and lst[3]=="OK") :
                    return True,lst[1] if lst[2]=="OK" else lst[2]
                else:
                    return False,data
        except Exception as e:
            print("==========readsn excption=======%s\n"%str(e))
            return False,str(e)
        finally:
            self.lock.release()
    """
    @param timeout wait for time
    @return tuple(bool, str)
            0:success True,failed False
            1:success: like "0xfffe",failed,it is source dataor error message
            source data: like "ReadDI\n\nNAK\n>"
    """
    def readDI(self,timeout=1):
        try:
            self.lock.acquire()
            if self.master.isOpen() :
                self.master.flushInput()
                if sys.version_info >= (3, 0):
                    command = ("ReadDI\r").encode("ascii")
                else:
                    command = "ReadDI\r"
                n=self.master.write(command)
                self.master.flushOutput()
                data = self.master.read(1)
                starttime = time.time()
                while True:
                    time.sleep(0.01)
                    n=self.master.inWaiting()
                    if(n==0):
                        break
                    data=data+self.master.read(n)
                    if time.time()-starttime>timeout:
                        break
                if sys.version_info >= (3, 0):
                    data = data.decode("utf-8")
                lst = data.split("\r\n")
                if((len(lst)==5 or len(lst)==4) and (lst[3]=="OK" or lst[2]=="OK")):
                        return True,lst[2] if lst[2]!="OK" else lst[1]
                else:
                    return False,data
            else:
                return False,"not open"
        except Exception as e:
            return False,str(e)
        finally:
            self.lock.release()
    """
    @param timeout wait for time
    @return tuple(bool, str)
            0:success True,failed False
            1:success: like "0xfffe",failed,it is source data or error message
            source data: like "ReadDO\n\nNAK\n>" "ReadDO\n\n0xfffe\n>"
    """
    def readDO(self,timeout=1):
        try:
            self.lock.acquire()
            if self.master.isOpen() :
                self.master.flushInput()
                if sys.version_info >= (3, 0):
                    command = ("ReadDO\r").encode("ascii")
                else:
                    command="ReadDO\r"
                n=self.master.write(command)
                self.master.flushOutput()
                data = self.master.read(1)
                starttime = time.time()
                while True:
                    time.sleep(0.01)
                    n=self.master.inWaiting()
                    if(n==0):
                        break
                    if time.time()-starttime>timeout:
                        break
                    data=data+self.master.read(n)
                if sys.version_info >= (3, 0):
                    data = data.decode("utf-8")
                lst = data.split("\r\n")
                if((len(lst)==5 or len(lst)==4) and (lst[3]=="OK" or lst[2]=="OK")):
                    return True,lst[2] if lst[2]!="OK" else lst[1]
                else:
                    return False,data
        except Exception as e:
            raise False(str(e))
        finally:
            self.lock.release()
    """
    @param index for IO Mapping.the value is 1~16
    @param timeout wait for time
    @return tuple(bool, str)
            0:success True,failed False
            1:success: like "0xfffe",failed,it is source data or error message
            source data: like "ReadDO\n\nNAK\n>" or "ReadDO\n\n0xfffe\n>"
    """
    def writeDO(self,index,status,timeout = 10):
        # print ("-------------------------",index,status)
        index=int(index)
        status=int(status)
        try:
            self.lock.acquire()
            if self.master.isOpen():
                self.master.flushInput()
                if sys.version_info >= (3, 0):
                    command = ("WriteDO %#.2x %#.2x\r"%(index,status)).encode("ascii")
                else:
                    command="WriteDO %#.2x %#.2x\r"%(index,status)
                self.master.write(command)
                data = self.master.read(1000)
                starttime = time.time()
                while True:
                    n=self.master.inWaiting()
                    if(n==0):
                        break 
                    if time.time()-starttime>timeout:
                        break
                    data=data+self.master.read(n)
                if sys.version_info >= (3, 0):
                    data = data.decode("utf-8")
                lst = data.split("\r\n")
                if lst[2]=="OK" or lst[1]=="OK":
                    return True,data
                else:
                    return False,data
        except Exception as e:
            print     ("Exception:%s"%(str(e))   )
            return False,"Exception:%s"%(str(e))
        finally:
            self.lock.release()

if __name__ == "__main__":
    innorev = InnorevController("/dev/ttyUSB1")
    print (innorev.checkConnect())
    print (innorev.ReadSN()[1]      )
    # print (innorev.WriteSN(2))
    # print(innorev.WriteID(3))WriteSN                         Interface/InnorevController.py:381
    # print(innorev.ReadID(1))/dev/ttyUSB0                  /dev/ttyUSB0
    print(innorev.readDI())
    # print (innorev.readDO())
    print (innorev.readSingle(1))
    print (innorev.readSingle(2))
    print (innorev.writeDO(8,1))