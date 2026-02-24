#!/usr/bin/python
# -*- coding: UTF-8 -*-
'''
Created on 2017-09-03

@author: zhouql

Add torque control by Ying Liao on 2017-11-23
'''
try:
  from InnorevModbus import *
except:
    from FixtureControl.InnorevModbus import *

# try:
#   from FixtureControl.IControl import *
# except:
#   from IControl import *

import time
import logging


class ASDServoController(InnorevModbus):
    '''
    classdocs
    '''

    def __init__(self, port, baudrate=115200):
        super(ASDServoController, self).__init__(port, baudrate)
        InnorevModbus.__init__(self, port)
        self.Pr306 = 0x030c
        self.Pr306_value = 0x0F2B #0x0F1E#0x0F2B #根据IO端子定义
        self.Pr407 = 0x040e
        self.Pr507 = 0x050E
        self.P112 = 0x0118
        self.P157 = 0x0172
        self.P208 = 0x0210
        # open p271
        self.P271 = 0x028e
        self.P400 = 0x0400
        self.P406 = 0x040C
        self.P409 = 0x0412
        self.P516 = 0x0520
        self.P520 = 0x0528
        self.P560 = 0x0578
        self.P603 = 0x0606      

        self.is_stop = False
        self.mode ="reg_trigger"
        self.ImmediateStop=False
        self.syncMove = True

        self.message = "wqnmlgb"

    def IntToHex(self, nbits, number):
        '''
        a number is divided to two 2-byte hex
        '''
        return (((number + (1 << nbits)) % (1 << nbits) & 0xffff), ((number + (1 << nbits)) % (1 << nbits) >> 16))



    def checkconnect(self, slave):
        try:
            if self.InnorevOpenSerial():
                self.getServoOnStatus(slave)
                return True
            else:
                return False
        except Exception as e:
            print("======in checked===========", str(e))
            return False

    def _degreeToPosition(self, degree, ratio, lead=360):
        '''
        x 1 round    :     10000
          10 rounds  :     360 degree

        y 1 round    :     10000
          40 rounds  :     360 degree

        z 1 round    :     10000
          40 rounds  :     360 degree
        '''
        degree = float(degree) / lead * 360
        return int(((degree * 10000) / 360) * ratio)

    def _openP271(self, slave):
        return self.InnorevWriteSingleRegister(slave, self.P208, 271)

    # set pr mode
    def openPr306(self, slave):
        return self.InnorevWriteSingleRegister(slave, self.Pr306, 0x0F)  #0x0D

    def _setAcceleration(self, slave, value):
        value = self.IntToHex(32, value)
        return self.InnorevWriteMultipleRegister(slave, self.P520, value)

    """
    value: speed value.max 6000,min 0.1
    """

    def _setSpeed(self, slave, value):
        value = value * 10
        value = self.IntToHex(32, value)
        return self.InnorevWriteMultipleRegister(slave, self.P560, value)

    def setZero(self, slave):
        self._openP271(slave)
        time.sleep(0.5)
        return self.InnorevWriteSingleRegister(slave, self.P271, 1)

    def MoveDegree(self, slave, degree, speed, acceleration, ratio=40, sync=True):
        self._setAcceleration(slave, acceleration)
        self._setSpeed(slave, speed)
        pos = self._degreeToPosition(degree, ratio)
        position = self.IntToHex(32, pos)
        self.InnorevWriteMultipleRegister(slave, self.P603, position)
        if self.mode == "DI_trigger" and self.InnorevWriteSingleRegister(slave, self.Pr407, 9):
            self.InnorevWriteSingleRegister(slave, self.Pr407, 1)
            while sync:
                data = self.InnorevReadHodlingRegister(slave, self.P409)
                speed_status = (data[0] >> 1) & 1
                arived_status = (data[0] >> 3) & 1
                if speed_status and arived_status:
                    return True
        elif self.mode=="reg_trigger":
              self.InnorevWriteSingleRegister(slave, self.Pr507, 1)
              while sync:
                  result = self.InnorevReadHodlingRegister(slave, self.Pr507)
                  data = self.InnorevReadHodlingRegister(slave,self.P409)
                  speed_status = (data[0]>>1)&1
                  arived_status = (data[0]>>3)&1
                  if result[0]==20001 or arived_status or self.ImmediateStop:
                    return True
        return True 

    def MoveLine(self, slave, degree, speed, acceleration, ratio=40, lead=10, sync=True):
        self._setAcceleration(slave, acceleration)
        self._setSpeed(slave, speed)
        pos = self._degreeToPosition(degree, ratio, lead)
        position = self.IntToHex(32, pos)
        self._getServoPosition(slave)
        self.InnorevWriteMultipleRegister(slave, self.P603, position)
        if self.mode == "DI_trigger" and self.InnorevWriteSingleRegister(slave, self.Pr407, 9):
            self.InnorevWriteSingleRegister(slave, self.Pr407, 1)
            while sync:
                data = self.InnorevReadHodlingRegister(slave, self.P409)
                speed_status = (data[0] >> 1) & 1
                arived_status = (data[0] >> 3) & 1
                # print ("data:",data)
                # print ("arived_status:",arived_status)
                # print ("speed_status:",speed_status)
                if speed_status and arived_status:
                    return True
        elif self.mode=="reg_trigger":
              self.InnorevWriteSingleRegister(slave, self.Pr507, 1)
              while sync:
                  result = self.InnorevReadHodlingRegister(slave, self.Pr507)
                  data = self.InnorevReadHodlingRegister(slave,self.P409)
                  speed_status = (data[0]>>1)&1
                  arived_status = (data[0]>>3)&1
                  # print ("result[0]:",result[0])
                  # print ("arived_status:",arived_status)
                  # print ("speed_status:",speed_status)
                  if result[0]==20001 or arived_status or self.ImmediateStop:
                    return True
        return True


    def _getServoPosition(self, slave):
        value_list = self.InnorevReadHodlingRegister(slave, self.P516, 2)
        pos = 0
        if value_list[1] > 32767:
            pos = value_list[1] * pow(2, 16) + value_list[0] - pow(2, 32)
        else:
            pos = value_list[1] * pow(2, 16) + value_list[0]
        return pos

    """
        @param target: target position
        @param ratio:  Deceleration ratio
        @param lead:  if move degree,lead=360.
    """
    def posCompare(self, slave, target, ratio, lead):
        time.sleep(0.5)
        dist = self._getServoPosition(slave)
        pos = asd._degreeToPosition(target, ratio, lead)
        source = asd.IntToHex(32, pos)
        print ("posCompare:",pos)
        return (dist[0] + 1 == source[0] and dist[1] == source[1]) or (
                    dist[0] == source[0] + 65535 and dist[1] == source[1] + 65535)

    def getServoOnStatus(self, slave):
        data = self.InnorevReadHodlingRegister(slave, self.P409)
        return data[0]

    def arivedStatus(self, slave):
        data = self.InnorevReadHodlingRegister(slave, self.P409)
        speed_status = (data[0] >> 1) & 1
        arived_status = (data[0] >> 3) & 1
        if speed_status and arived_status:
            return True
        return False

    def IsSetZeroStatus(self, slave):
        data = self.InnorevReadHodlingRegister(slave, self.P409)
        status = (data[0] >> 2) & 1
        if status:
            return True
        return False

    def stop(self, slave):
        if self.InnorevWriteSingleRegister(slave, self.Pr407, 5):
            return self.InnorevWriteSingleRegister(slave, self.Pr407, 1)
        return False

    def SetServoRtuEnabled(self, slave):
        return self.InnorevWriteSingleRegister(slave, self.Pr407, 1)

    def SetServoRtuDisabled(self, slave):
        return self.InnorevWriteSingleRegister(slave, self.Pr407, 0)

    def SetServoPrMode(self, slave):
        return self.InnorevWriteSingleRegister(slave, self.Pr407, 2)

    def MovePosition(self, slave, pos, sync=True):
        position = self.IntToHex(32, pos)
        self.InnorevWriteSingleRegister(slave, self.Pr407, 0xC0)
        self.InnorevWriteMultipleRegister(slave, self.P603, position)
        if self.InnorevWriteSingleRegister(slave, self.Pr407, 0x44):
            while sync:
                pos1 = self._getServoPosition(slave)
                if (pos1 <= pos + 2) and (pos1 >= pos - 2):
                    return True
            return True
        else:
            return False

    def A3MovePosition(self, slave, pos, sync=True):
        self.is_stop = False
        position = self.IntToHex(32, pos)
        self.InnorevWriteSingleRegister(slave, self.Pr407, 0x14)
        self.InnorevWriteMultipleRegister(slave, self.P603, position)
        if self.InnorevWriteSingleRegister(slave, self.Pr407, 0x18):
            while sync:
                if True == self.is_stop:
                    break
                time.sleep(.3)
                pos1 = self._getServoPosition(slave)
                # print pos1,pos
                if (pos1 <= pos + 2) and (pos1 >= pos - 2):
                    return True
            return True
        else:
            return False

    def CheckInPosition(self, slave):
        while True:
            data = self.InnorevReadHodlingRegister(slave, self.P409)
            if data[0] == 27:
                return True

    def SetServoTorgueMode(self, slave):
        return self.InnorevWriteSingleRegister(slave, self.Pr407, 0x20)

    def SetLowTorguePercent(self, slave, torguePercent):
        if ((torguePercent >= -300) and (torguePercent <= 300)):
            return self.InnorevWriteSingleRegister(slave, self.P112, torguePercent)
        else:
            logging.error('Torgue value ' + str(torguePercent) + ' is out of range(-300,300)')
            return False

    def SetServoTorgueControl(self, slave):
        return self.InnorevWriteSingleRegister(slave, self.Pr407, 0x60)

    def SetP306Mode(self, slave):
        return self.InnorevWriteSingleRegister(slave, self.Pr306, 0xF4)

    def SetA3P306Mode(self, slave):
        return self.InnorevWriteSingleRegister(slave, self.Pr306, 0x1E)

    def A3ClearAlarm(self, slave):
        return self.InnorevWriteSingleRegister(slave, self.Pr407, 0x12)

    def ClosePrMode(self, slave):
        return self.InnorevWriteSingleRegister(slave, self.Pr407, 0xC0)

    def MoveToZeroPosition(self, slave):
        self.InnorevWriteSingleRegister(slave, self.Pr407, 0xC0)
        self.InnorevWriteSingleRegister(slave, self.Pr407, 0x50)
        pos = self._getServoPosition(slave)
        while (True):
            time.sleep(1)
            pos1 = self._getServoPosition(slave)
            if ((pos - 2) <= pos1) and ((pos + 2) >= pos1):
                return True
            else:
                pos = pos1

    def A3MoveToZeroPosition(self, slave):
        self.InnorevWriteSingleRegister(slave, self.Pr407, 0x14)
        time.sleep(1)
        self.InnorevWriteSingleRegister(slave, self.Pr407, 0x08)
        pos = self._getServoPosition(slave)
        while (True):
            time.sleep(1)
            pos1 = self._getServoPosition(slave)
            # print pos1, pos
            if ((pos - 2) <= pos1) and ((pos + 2) >= pos1):
                return True
            else:
                pos = pos1

    def test_function(self,msg):
        print("***%s***"%msg)


if __name__ == "__main__":
    asd = ASDServoController("/dev/ttyUSB0")
    slave_address = 1
    print ("Check Connect:",asd.checkconnect(slave_address))
    # print(asd.MoveLine(1, 3, 200, 200, 1, 2, True))


















    # print ("OpenPr36:",asd.openPr306(slave_address))
    # # print ("setZero:",asd.setZero(slave_address))
    # print ("Enable:",asd.SetServoRtuEnabled(slave_address))
    # time.sleep(1)
    # print ("Disable:",asd.SetServoRtuDisabled(1))
    # time.sleep(1)
    # print ("Enable:",asd.SetServoRtuEnabled(slave_address))
    #
    # print ("getServoOnStatus:",asd.getServoOnStatus(slave_address))
    # print ("Is Set Zero:",asd .IsSetZeroStatus(slave_address))
    #
    # print ("Move Line_10:",asd.MoveLine(slave_address,5,2000,200,1,2,True))  #args (self, slave, degree, speed, acceleration, ratio=40, sync=True):
    # time.sleep(3)
    #
    # print ("Move Line_0:",asd.MoveLine(slave_address,0,4000,2000,1,2,True))
    # time.sleep(3)
    # print ("MoveDegree_180:",asd.MoveDegree(slave_address,720,2000,200,1,True)) # args (self, slave, degree, speed, acceleration, ratio=40, sync=True):
    # time.sleep(3)
    # print ("MoveDegree_0:",asd.MoveDegree(slave_address,0,2000,200,1))
    # time.sleep(3)
    # print (asd._getServoPosition(1))
    #
    # # print ("Move Line_10:",asd.MoveLine(slave_address,0,2000,200,1,2,False))  #args (self, slave, degree, speed, acceleration, ratio=40, sync=True):
    #
    # # print ("MoveDegree_180:",asd.MoveDegree(slave_address,0,2000,200,1,False)) # args (self, slave, degree, speed, acceleration, ratio=40, sync=True):
    #
