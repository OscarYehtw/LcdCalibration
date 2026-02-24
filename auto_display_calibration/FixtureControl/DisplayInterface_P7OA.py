# !/usr/bin/python
# -*- coding: UTF-8 -*-
'''
Created on 2020-10-09

@author: lzq
'''
import serial.tools.list_ports
import platform
import time
from datetime import datetime
import subprocess as sub
import yaml
import os, sys
import datetime
try:
    from FixtureControl.InnorevController import InnorevController
    from FixtureControl.ASDServoController import ASDServoController
except:
    from InnorevController import InnorevController
    from ASDServoController import ASDServoController

"""changed by luzhiqiang 2021-04-01 for P7 station
1. add init_control()/cleanup_control() function to intergration.

"""


"""changed by luzhiqiang 2021-02-04 for P7 station
1. add typec_test() function.
2. update spin_move_to_test()/spin_move_to_home() function.
3. update io position

"""

"""changed by luzhiqiang 2020-11-26
1. add config move motor.

"""

"""changed by luzhiqiang 2020-11-25
1. add reset return value.

"""

"""changed by luzhiqiang 2020-11-13
1. update remove  display cal.
2. reset function add return True or False.
"""

log_path = os.path.join(os.path.expanduser('~'), 'Test_Log')

CURRENT_DIR = os.path.dirname(__file__)
sys.path.append(CURRENT_DIR)
sys.path.append(os.path.split(CURRENT_DIR)[0])
CONF_FILE_PATH = os.path.join(CURRENT_DIR, 'config.yaml')

class Log(object):
    """docstring for Log"""
    def __init__(self,  filename='./log'):
        self.filename = filename

    def write_log(self, message):
        path = self.filename
        if os.path.exists(path) == False:
            os.makedirs(path)
        strtime = time.strftime("%Y-%m-%d", time.localtime())
        log_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        filename = path + '/'+ strtime + '.txt'
        # print (filename)
        fp = open(filename, 'ab')
        log = log_time + ':' + str(message)
        log = log.encode('unicode-escape')
        fp.write(log + b'\r\n')
        fp.close()

class DisplayInterface_P7OA(object):
    def __init__(self):
        self.innorev = None
        self.asd = None
        self.config = None
        self._config_path = CONF_FILE_PATH
        self.log = None
        self.log = Log(log_path)
        self._getConfigrution()
        self.connect()
        self.OA_reset()

    def connect(self):
        lists = self.getSerials()
        print(lists)
        for port in lists:
            try:
                innorev = InnorevController(port.strip())
                if innorev.checkConnect():
                    self.innorev = innorev
                    print("=============connect io card  success!=========%s" % port)
                    self.log.write_log("=============connect io card  success!=========%s" % port)
                    # return True
                    lists.remove(port)
                else:
                    innorev.close()
                    continue
            except Exception as e:
                print(str(e))
        # self.log.write_log("=============connect io card  disconnect!=========" )
        for port in lists:
            try:
                asd = ASDServoController(port.strip())
                if asd.checkconnect(1):
                    self.asd = asd
                    print("=============connect asd control  success!=========%s" % port)
                    self.log.write_log("=============connect asd control  success!=========%s" % port)
                    lists.remove(port)
                else:
                    asd.close()
                    continue
            except Exception as e:
                print(str(e))
        # return False

    def getSerials(self):
        '''
        get USB port
        '''
        port_list = serial.tools.list_ports.comports()
        lists = list()
        system = platform.system()
        if (system == "Linux"):
            for port in port_list:
                port = str(port.device)
                if ("USB" in port):
                    lists.append(port)
        elif system == "Darwin":
            print(port_list)
            for port in port_list:
                port = str(port.device)
                if ("cu.usb" in port):
                    lists.append(port)
        else:
            for port in port_list:
                if ("Port" in str(port)):
                    port = str(port.device)
                    lists.append(port)
        return lists

    def _getConfigrution(self):
        '''
        get yaml config
        '''
        with open(self._config_path, mode='r') as fp:
            print(self._config_path)
            config = yaml.safe_load(fp)
        config_path = config['config']['FATP-DISP-OA']['config_path']
        # self.log = Log(config['config']['log_path'])
        self.log.write_log('config_path:{}'.format(config_path))


        if not os.path.exists(config_path):
            config_path = os.path.join(CURRENT_DIR, "displayP7OA_config.yaml")
            print(config_path, "====1===")
            if not os.path.exists(config_path):
                raise Exception('Not find config file, please check')
        with open(config_path, mode='r') as f:
            print(config_path)
            self.config = yaml.safe_load(f)
        print(self.config,"==================")

    def innorev_read_Single(self, index):
        '''
        read io card single, if num == 'NAK', try again
        '''
        num, data = self.innorev.readSingle(index)
        if num == True or num == False :
            return num, data
        else:
            number = 1
            while 1:
                num, data = self.innorev.readSingle(index)
                if num == True or num == False:
                    print('+++++io card read again+++++')
                    self.log.write_log('+++++io card read again+++++')
                    return num, data
                elif number == 4:
                    raise Exception('read io card value error')
                self.log.write_log('====io card read again====read number: %s, num,data:%s %s' % (number, num, data))
                time.sleep(0.1)
                number += 1

    #interface 3up OA

    def init_control(self, index=1):
        msg = ''
        ret = self.check_door_status()
        if not ret:
            msg = 'door is not close'
            return ret, msg
        ret = self.typec_test()
        if not ret:
            msg = 'Typec insert fail'
            return ret, msg
        return True,"OK"

    def cleanup_control(self, index=1):
        return self.OA_reset(),""

    def OA_reset(self):
        flag = self.spin_move_to_home()
        if flag == False:
            self.log.write_log("OA spin_move_to_home result:{}".format(flag))
            return False
        flag = self.typec_reset()
        if flag == False:
            self.log.write_log("OA typec_reset result:{}".format(flag))
            return False
        motor_disable = self.config['motor']['motor_disable']
        if motor_disable == False:
            flag = self.move_to_center()
            if flag == False:
                self.log.write_log("OA motor_move to center result:{}".format(flag))
                return False
        self.log.write_log("OA reset  result:{}".format(flag))
        return True

    def move_to_center(self):
        degree = self.config['motor']['center_position']
        ret = self.MoveLine(degree)
        self.log.write_log("OA move to center result:{}".format(ret))
        return ret

    def move_to_down(self):
        degree = self.config['motor']['down_position']
        ret = self.MoveLine(degree)
        self.log.write_log("OA move to down result:{}".format(ret))
        return ret

    def MoveLine(self, degree):
        # MoveLine(self, slave, degree, speed, acceleration, ratio=40, lead=10, sync=True)
        speed = self.config['motor']['speed']
        acceleration = self.config['motor']['acceleration']
        ratio = self.config['motor']['ratio']
        lead = self.config['motor']['lead']

        ret = self.asd.MoveLine(1, degree, speed, acceleration, ratio, lead, sync=True)
        return ret

    def typec_test(self, index=None):
        ret = self.clamp_test()
        if ret:
            self.typec_control_open()
            number = 0
            while True:
                number = number + 1
                ret = self.check_typec_in_test_status()
                if ret:
                    self.log.write_log("OA typec to test success")
                    return ret
                if (number > 30):
                    self.log.write_log("OA typec to test time out,ret{}".format(ret))
                    return ret
                else:
                    time.sleep(0.1)
        else:
            return False

    def typec_reset(self):
        return self.typec_control_close() and self.clamping_control_close()

    def clamp_test(self):
        self.clamping_control_open()
        number = 0
        while True:
            number = number + 1
            ret = self.check_DUT_clamping_in_test_status()
            if ret:
                self.log.write_log("OA clamp to test success")
                return ret
            if (number > 30):
                self.log.write_log("OA clamp to test time out,ret{}".format(ret))
                return ret
            else:
                time.sleep(0.1)

    def clamp_home(self):
        self.clamping_control_close()
        number = 0
        while True:
            number = number + 1
            ret = self.check_DUT_clamping_in_home_status()
            if ret:
                self.log.write_log("OA clamp to home success")
                return ret
            if (number > 30):
                self.log.write_log("OA clamp to home time out,ret{}".format(ret))
                return ret
            else:
                time.sleep(0.1)

    def spin_move_to_test(self):
        self.spin_test_control_open()
        self.spin_home_control_close()
        number = 0
        while True:
            number = number + 1
            ret = self.check_spin_in_test_status()
            if ret:
                self.log.write_log("OA spin  to test success")
                return ret
            if (number > 30):
                self.log.write_log("OA spin to test time out,ret{}".format(ret))
                return ret
            else:
                time.sleep(0.1)

    def spin_move_to_home(self):
        self.spin_test_control_close()
        self.spin_home_control_open()
        number = 0
        while True:
            number = number + 1
            ret = self.check_spin_in_home_status()
            if ret:
                self.log.write_log("OA spin to home success")
                return ret
            if (number > 30):
                self.log.write_log("OA spin to home time out,ret{}".format(ret))
                return ret
            else:
                time.sleep(0.1)

    # Display cal OA
    # input
    def check_start_status(self):
        num, data = self.innorev_read_Single(self.config['boardIO_OA']['_ADDRESS_START_BUTTON_STATUS'])
        return True if not num else False

    def check_door_status(self):
        num, data = self.innorev_read_Single(self.config['boardIO_OA']['_ADDRESS_DOOR_STATUS'])
        return True if not num else False

    def check_spin_in_home_status(self):
        num, data = self.innorev_read_Single(self.config['boardIO_OA']['_ADDRESS_SPIN_HOME_STATUS'])
        return True if not num else False

    def check_spin_in_test_status(self):
        num, data = self.innorev_read_Single(self.config['boardIO_OA']['_ADDRESS_SPIN_TEST_STATUS'])
        return True if not num else False

    def check_DUT_clamping_in_home_status(self):
        num, data = self.innorev_read_Single(self.config['boardIO_OA']['_ADDRESS_CLAMPING_HOME_STATUS'])
        return True if not num else False

    def check_DUT_clamping_in_test_status(self):
        num, data = self.innorev_read_Single(self.config['boardIO_OA']['_ADDRESS_CLAMPING_TEST_STATUS'])
        return True if not num else False

    def check_typec_in_home_status(self):
        num, data = self.innorev_read_Single(self.config['boardIO_OA']['_ADDRESS_TYPEC_HOME_STATUS'])
        return True if not num else False

    def check_typec_in_test_status(self):
        num, data = self.innorev_read_Single(self.config['boardIO_OA']['_ADDRESS_TYPEC_TEST_STATUS'])
        return True if not num else False

    '''output'''
    def red_light_control_open(self):
        s, data = self.innorev.writeDO(self.config['boardIO_OA']['_ADDRESS_RED_LIGHT_1_CONTROL'], 0)
        return s

    def red_light_control_close(self):
        s, data = self.innorev.writeDO(self.config['boardIO_OA']['_ADDRESS_RED_LIGHT_1_CONTROL'], 1)
        return s

    def green_light_control_open(self):
        s, data = self.innorev.writeDO(self.config['boardIO_OA']['_ADDRESS_GREEN_LIGHT_1_CONTROL'], 0)
        return s

    def green_light_control_close(self):
        s, data = self.innorev.writeDO(self.config['boardIO_OA']['_ADDRESS_GREEN_LIGHT_1_CONTROL'], 1)
        return s

    def spin_test_control_open(self):
        s, data = self.innorev.writeDO(self.config['boardIO_OA']['_ADDRESS_SPIN_TEST_CONTROL'], 0)
        return s

    def spin_test_control_close(self):
        s, data = self.innorev.writeDO(self.config['boardIO_OA']['_ADDRESS_SPIN_TEST_CONTROL'], 1)
        return s

    def spin_home_control_open(self):
        s, data = self.innorev.writeDO(self.config['boardIO_OA']['_ADDRESS_SPIN_HOME_CONTROL'], 0)
        return s

    def spin_home_control_close(self):
        s, data = self.innorev.writeDO(self.config['boardIO_OA']['_ADDRESS_SPIN_HOME_CONTROL'], 1)
        return s

    def clamping_control_open(self):
        s, data = self.innorev.writeDO(self.config['boardIO_OA']['_ADDRESS_CLAMPING_CONTROL'], 0)
        return s

    def clamping_control_close(self):
        s, data = self.innorev.writeDO(self.config['boardIO_OA']['_ADDRESS_CLAMPING_CONTROL'], 1)
        return s

    def typec_control_open(self):
        s, data = self.innorev.writeDO(self.config['boardIO_OA']['_ADDRESS_TYPEC_CONTROL'], 0)
        return s

    def typec_control_close(self):
        s, data = self.innorev.writeDO(self.config['boardIO_OA']['_ADDRESS_TYPEC_CONTROL'], 1)
        return s


if __name__ == "__main__":
    dis = DisplayInterface_P7OA()
    while True:
        dis.init_control()
        dis.cleanup_control()

    exit()
    print(dis.typec_test())
    print(dis.spin_move_to_test())
    time.sleep(1)
    print(dis.spin_move_to_home())
    print(dis.move_to_center())
    print(dis.move_to_down())

    print(dis.OA_reset())
