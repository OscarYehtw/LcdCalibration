#!/usr/bin/python
# -*- coding: UTF-8 -*-
'''
Created on 2017-09-03

@author: zhouql
'''
try:
    from FixtureControl.InnorevModbus import *
except:
    from InnorevModbus import *
import time
import logging
import sqlite3
import serial
import threading
class MoonsController(InnorevModbus):
    '''
    classdocs
    '''
    
    def __init__(self,port):
        InnorevModbus.__init__(self,port)
        self.MoonsHomeStatus = 0x3C     #40061
        self.MoonsPositionAddress = 0x1B
        self.MoonsStatusAddress = 0x01    #40002 -40001
        self.MoonsImmediateControlAddress = 0x7C #40125 - 40001
    def checkConnect(self,slave=1):
        try:
            if self.InnorevOpenSerial():
                data = self.CheckHomeStatus(slave)
                return True
            else:
                return False
        except Exception as e:
            #print e.message
            return False
    def IntToHex(self,nbits, number):
        '''
        a number is divided to two 2-byte hex
        '''
        return (((number + (1 << nbits)) % (1 << nbits) & 0xffff) ,((number + (1 << nbits)) % (1 << nbits) >> 16))
    def GetMoonsStatus(self,slave):
        '''
        0x0001   ---    Motor Enabled(Motor Disabled if this bit = 0)
        0x0002   ---    Sampling(for Quick Tuner)
        0x0004   ---    Drive Fault(check Alarm Code)
        0x0008   ---    In position(Motor is in position)
        0x0010   ---    Moving(Motor is moving)
        0x0020   ---    Jogging(currently in jog mode)
        0x0040   ---    Stopping(in the process of stopping from a stop command)
        0x0100   ---    Saving(parameter data is being saved)
        0x0200   ---    Alarm present(check Alarm Code)
        0x0400   ---    Homing(executing a WT command)
        0x0800   ---    Stopping(in the process of stopping from a stop command)
        0x1000   ---    Wizard running(Timing Wizard is running)
        0x2000   ---    Checking encoder(Timing Wizard is running)
        0x4000   ---    Q program is running
        0x8000   ---    Initializing(happens at power up)
        '''
        data = self.InnorevReadHodlingRegister(slave, self.MoonsStatusAddress, 1)
        return data
    def CheckHomeStatus(self,slave):
        data = self.InnorevReadHodlingRegister(slave, self.MoonsHomeStatus, 2)
        if((data[0] == 1 or data[1] == 1)):
            return True
        else:
            return False
    def SetMoonsHome(self,slave=1):
        para_list = []
        para_list.append(0x78)
        para_list.append(0x01)
        if(True == self.InnorevWriteMultipleRegister(slave, self.MoonsImmediateControlAddress, para_list)):
            IsInPosition = self.CheckHomeStatus(slave)
            while(False == IsInPosition):
                time.sleep(0.1)
                IsInPosition = self.CheckHomeStatus(slave)
            return True
    def SetMoonsZeroPosition(self,slave,para_list):
        if(True == self.InnorevWriteMultipleRegister(slave,self.MoonsImmediateControlAddress, para_list)):
            para_list1 = []
            para_list1.append(0x98)
            para_list1.append(para_list[1])
            if(True == self.InnorevWriteMultipleRegister(slave,self.MoonsImmediateControlAddress, para_list1)):
                para_list2 = []
                para_list2.append(0xA5)
                para_list2.append(para_list[1])
                if(True == self.InnorevWriteMultipleRegister(slave,self.MoonsImmediateControlAddress, para_list1)):
                    return True
                else:
                    return False
    def SetMoonsImmediatelyMove(self,slave):
        return self.InnorevWriteSingleRegister(slave, self.MoonsImmediateControlAddress, 0x67)
    def SetMoonsImmediatelyStop(self,slave):
        return self.InnorevWriteSingleRegister(slave, self.MoonsImmediateControlAddress, 0xE1)
    def SetMoonsPosition(self,slave,para_list):
        if( True == self.InnorevWriteMultipleRegister(slave, self.MoonsPositionAddress, para_list)):
            if(True == self.SetMoonsImmediatelyMove(slave)):
                return True
            else:
                return False
    def _degreeToPosition(self, degree, ratio,lead=360):
        '''
        x 1 round    :     10000
          10 rounds  :     360 degree

        y 1 round    :     10000
          40 rounds  :     360 degree

        z 1 round    :     10000
          40 rounds  :     360 degree
        '''
        degree = float(degree)/lead*360
        return int(((degree * 10000) / 360)*ratio)
    def MoveDegree(self,slave,position,speed,acceleration,deceleration,ratio=1):
        position = self._degreeToPosition(position,ratio)
        para_list = []
        para_list.append(acceleration)
        para_list.append(deceleration)
        para_list.append(speed)
        (var1,var2) = self.IntToHex(32, position)
        para_list.append(var1)
        para_list.append(var2)
        number = 1
        if( True == self.SetMoonsPosition(slave,para_list)):
            data = self.GetMoonsStatus(slave)
            while(int(data[0]) < 9):
                number = number + 1
                if(number > 15):
                   break
                else:
                    time.sleep(0.1)
                    data = self.GetMoonsStatus(slave)
            return True
        else:
            return False
    def MoveLine(self,slave,position,speed,acceleration,deceleration,ratio=40,lead=10):
        position = self._degreeToPosition(position,1,lead)
        para_list = []
        para_list.append(acceleration)
        para_list.append(deceleration)
        para_list.append(speed)
        (var1,var2) = self.IntToHex(32, position)
        para_list.append(var1)
        para_list.append(var2)
        if( True == self.SetMoonsPosition(slave,para_list)):
            data = self.GetMoonsStatus(slave)
            while(data[0] != 9):
                time.sleep(0.1)
                data = self.GetMoonsStatus(slave)
            return True
        else:
            return False
if __name__=="__main__":
    asd = MoonsController('/dev/ttyUSB1')
    print (asd.checkConnect(1))





    # asd.SetMoonsHome(1)
    # time.sleep(2)
    # asd.MoveLine(1,1)
    # asd.MoveLine(1,145, 300, 300, 300, 1)
    # asd.MoveLine(1, 330, 300, 300, 300, ratio=1, lead=10)
    # # asd.SetxMoonsImmediatelyStop(1)
    # print asd.GetMoonsStatus(1)