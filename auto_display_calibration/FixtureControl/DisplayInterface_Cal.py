# !/usr/bin/python
# -*- coding: UTF-8 -*-
'''
Created on 2020-10-09

@author: lzq
'''

'''
20210330
1.add init_control/cleanup_control function to intergration
'''

'''
20210121
1.add reset in __init__()
'''

'''
20201120
1.update all interface function add input index.
'''


'''
20201119 
1.update get_hyperion_id() function add input index.
2.update get_dut_port() function add input index.
'''

'''
20201113 
1.update remove Display OA
'''
import serial.tools.list_ports
import platform
import time
from datetime import datetime
import subprocess as sub
import yaml
import os, sys
import datetime

from FixtureControl.InnorevController import InnorevController
# from FixtureControl.ASDServoController import ASDServoController

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

class DisplayInterface_Cal(object):
    def __init__(self):
        self.innorev1 = None
        self.innorev2 = None
        self.asd = None
        self.config = None
        self._config_path = CONF_FILE_PATH
        self.log = None
        self.log = Log(log_path)
        self._getConfigrution()
        self.connect()
        self.typec_reset(1)
        self.typec_reset(2)
        self.typec_reset(3)
        # self.reset()

    def connect(self):
        lists = self.getSerials()
        print(lists)
        for port in lists:
            try:
                innorev = InnorevController(port.strip())
                if innorev.checkConnect():
                    _, sn = innorev.ReadSN()
                    if sn == '0001':
                        self.innorev1 = innorev
                        print("=============connect io card 1 success!=========%s" % port)
                        self.log.write_log("=============connect io card 1 success!=========%s" % port)
                    elif sn == '0002':
                        self.innorev2 = innorev
                        print("=============connect io card 2 success!=========%s" % port)
                        self.log.write_log("=============connect io card 2 success!=========%s" % port)
                else:
                    innorev.close()
                    continue
            except Exception as e:
                print(str(e))


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
        config_path = config['config']['FATP-DISP-CAL']['config_path']
        # self.log = Log(config['config']['log_path'])
        self.log.write_log('config_path:{}'.format(config_path))


        if not os.path.exists(config_path):
            config_path = os.path.join(CURRENT_DIR, "displayCal_config.yaml")
            print(config_path, "====1===")
            if not os.path.exists(config_path):
                raise Exception('Not find config file, please check')
        else:
            with open(config_path, mode='r') as f:
                print(config_path)
                self.config = yaml.safe_load(f)

    def innorev1_read_Single(self, index):
        '''
        read io card single, if num == 'NAK', try again
        '''
        num, data = self.innorev1.readSingle(index)
        if num == True or num == False :
            return num, data
        else:
            number = 1
            while 1:
                num, data = self.innorev1.readSingle(index)
                if num == True or num == False:
                    print('+++++io card 1 read again+++++')
                    self.log.write_log('+++++io card 1 read again+++++')
                    return num, data
                elif number == 4:
                    raise Exception('read io card value error')
                self.log.write_log('====io card 1 read again====read number: %s, num,data:%s %s' % (number, num, data))
                time.sleep(0.1)
                number += 1

    def innorev2_read_Single(self, index):
        '''
        read io card single, if num == 'NAK', try again
        '''
        num, data = self.innorev2.readSingle(index)
        if num == True or num == False :
            return num, data
        else:
            number = 1
            while 1:
                num, data = self.innorev2.readSingle(index)
                if num == True or num == False:
                    print('+++++io card 2 read again+++++')
                    self.log.write_log('+++++io card 2 read again+++++')
                    return num, data
                elif number == 4:
                    raise Exception('read io card value error')
                self.log.write_log('====io card 1 read again====read number: %s, num,data:%s %s' % (number, num, data))
                time.sleep(0.1)
                number += 1
    #interface 3up

    def init_control(self, index):
        msg = 'Init control success'
        ret = self.check_position_status(index)
        if not ret:
            msg = 'DUT not in position'
            return ret, msg
        ret = self.typec_test(index)
        if not ret:
            msg = 'Typec insert issue'
            return ret, msg
        return ret, msg

    def cleanup_control(self, index):
        msg = 'cleanup control success'
        ret = self.typec_reset(index)
        if not ret:
            msg = 'cleanup control fail'
            return ret, msg
        return ret, msg

    def check_position_status(self, index):
        if index == 1:
            return self.check_DUT_1_status()
        elif index == 2:
            return self.check_DUT_2_status()
        elif index == 3:
            return self.check_DUT_3_status()

    def typec_reset(self, index):
        if index == 1:
            ret_1 = self.typec_control_1_close()
            self.clamping_control_test_1_close()
            clamping_ret_1 = self.clamping_control_home_1_open()
            self.log.write_log("reset result:typec:{}; clamping:{}".
                               format(ret_1, clamping_ret_1))
        elif index == 2:
            ret_2 = self.typec_control_2_close()
            self.clamping_control_test_2_close()
            clamping_ret_2 = self.clamping_control_home_2_open()
            self.log.write_log("reset result:typec:{}; clamping:{}".
                               format(ret_2, clamping_ret_2))
        elif index == 3:
            ret_3 = self.typec_control_3_close()
            self.clamping_control_test_3_close()
            clamping_ret_1 = self.clamping_control_home_3_open()
            self.log.write_log("reset result:typec:{}; clamping:{}".
                               format(ret_3, clamping_ret_1))

    def typec_test(self, index):
        if index == 1:
            ret = self.clamping_1_test()
            if ret:
                ret = self.typec_1_test()
                return ret
            return ret

        elif index == 2:
            ret = self.clamping_2_test()
            if ret:
                ret = self.typec_2_test()
                return ret
            return ret

        elif index == 3:
            ret = self.clamping_3_test()
            if ret:
                ret = self.typec_3_test()
                return ret
            return ret

    # def clamping_test(self):
    #     # dut_flag_1 = self.check_DUT_1_status()
    #     # dut_flag_2 = self.check_DUT_2_status()
    #     # dut_flag_3 = self.check_DUT_3_status()
    #     # ret_1, ret_2, ret_3 = False, False, False
    #
    #     ret_1 = self.clamping_1_test()
    #     ret_2 = self.clamping_2_test()
    #     ret_3 = self.clamping_3_test()
    #     return ret_1, ret_2, ret_3

    def get_hyperion_id(self, index):
        '''input index value 1, 2, 3 '''
        hyperion_port = ''
        if index == 1:
            hyperion_port = self.config['hyperion']['hyperion_1']
        elif index == 2:
            hyperion_port = self.config['hyperion']['hyperion_2']
        elif index == 3:
            hyperion_port = self.config['hyperion']['hyperion_3']
        return hyperion_port

    def get_dut_port(self, index):
        '''input index value 1, 2, 3 '''
        dut_port = ''
        if index == 1:
            dut_port = self.config['DUT_Port']['dut_1']
        elif index == 2:
            dut_port = self.config['DUT_Port']['dut_2']
        elif index == 3:
            dut_port = self.config['DUT_Port']['dut_3']
        return dut_port

    def typec_1_test(self):

        self.typec_control_1_open()
        number = 0
        while True:
            number = number + 1
            ret_1 = self.check_typec_in_test_1_status()
            if ret_1:
                self.log.write_log("typec move to test success")
                return ret_1
            if (number > 30):
                self.log.write_log("typec move to test time out,ret_1{}".format(ret_1))
                return ret_1
            else:
                time.sleep(0.1)

    def typec_2_test(self):
        self.typec_control_2_open()
        number = 0
        while True:
            number = number + 1
            ret_2 = self.check_typec_in_test_2_status()
            if ret_2:
                self.log.write_log("typec move to test success")
                return ret_2
            if (number > 30):
                self.log.write_log("typec move to test time out,ret_2{}".format(ret_2))
                return ret_2
            else:
                time.sleep(0.1)

    def typec_3_test(self):
        self.typec_control_3_open()
        number = 0
        while True:
            number = number + 1
            ret_3 = self.check_typec_in_test_3_status()
            if ret_3:
                self.log.write_log("typec move to test success")
                return ret_3
            if (number > 30):
                self.log.write_log("typec move to test time out,ret_3{}".format(ret_3))
                return ret_3
            else:
                time.sleep(0.1)

    def clamping_1_test(self):
        self.clamping_control_test_1_open()
        self.clamping_control_home_1_close()
        number = 0
        while True:
            number = number + 1
            ret_1 = self.check_DUT_clamping_in_test_1_status()
            if ret_1 :
                self.log.write_log("clamping DUT to test success")
                return ret_1
            if (number > 30):
                self.log.write_log("clamping DUT to test time out,ret_1{}".format(ret_1))
                return ret_1
            else:
                time.sleep(0.1)

    def clamping_2_test(self):
        self.clamping_control_test_2_open()
        self.clamping_control_home_2_close()
        number = 0
        while True:
            number = number + 1
            ret_2 = self.check_DUT_clamping_in_test_2_status()
            if ret_2 :
                self.log.write_log("clamping DUT to test success")
                return ret_2
            if (number > 30):
                self.log.write_log("clamping DUT to test time out,ret_2{}".format(ret_2))
                return ret_2
            else:
                time.sleep(0.1)

    def clamping_3_test(self):
        self.clamping_control_test_3_open()
        self.clamping_control_home_3_close()
        number = 0
        while True:
            number = number + 1
            ret_3 = self.check_DUT_clamping_in_test_3_status()
            if ret_3 :
                self.log.write_log("clamping DUT to test success")
                return ret_3
            if (number > 30):
                self.log.write_log("clamping DUT to test time out,ret_3{}".format(ret_3))
                return ret_3
            else:
                time.sleep(0.1)

    # input
    def check_DUT_1_status(self):
        # num, data = self.innorev1_read_Single(self.config['boardIO']['_ADDRESS_CHECK_DUT_1_STATUS'])
        num, data = self.innorev1_read_Single(self.config['boardIO']['_ADDRESS_CHECK_DUT_1_STATUS'])
        return True if not num else False

    def check_DUT_2_status(self):
        num, data = self.innorev1_read_Single(self.config['boardIO']['_ADDRESS_CHECK_DUT_2_STATUS'])
        return True if not num else False

    def check_DUT_3_status(self):
        num, data = self.innorev1_read_Single(self.config['boardIO']['_ADDRESS_CHECK_DUT_3_STATUS'])
        return True if not num else False

    def check_DUT_position_status(self):
        num, data = self.innorev1_read_Single(self.config['boardIO']['_ADDRESS_DUT_POSITION_STATUS'])
        return True if not num else False

    def check_start_1_status(self):
        num, data = self.innorev1_read_Single(self.config['boardIO']['_ADDRESS_START_BUTTON_1_STATUS'])
        return True if not num else False

    def check_typec_in_home_1_status(self):
        num, data = self.innorev1_read_Single(self.config['boardIO']['_ADDRESS_TYPEC_IN_HOME_1_STATUS'])
        return True if not num else False

    def check_typec_in_test_1_status(self):
        num, data = self.innorev1_read_Single(self.config['boardIO']['_ADDRESS_TYPEC_IN_TEST_1_STATUS'])
        return True if not num else False

    def check_DUT_clamping_in_home_1_status(self):
        num, data = self.innorev1_read_Single(self.config['boardIO']['_ADDRESS_DUT_CLAMPING_IN_HOME_1_STATUS'])
        return True if not num else False

    def check_DUT_clamping_in_test_1_status(self):
        num, data = self.innorev1_read_Single(self.config['boardIO']['_ADDRESS_DUT_CLAMPING_IN_TEST_1_STATUS'])
        return True if not num else False

    def check_start_2_status(self):
        num, data = self.innorev1_read_Single(self.config['boardIO']['_ADDRESS_START_BUTTON_2_STATUS'])
        return True if not num else False

    def check_typec_in_home_2_status(self):
        num, data = self.innorev1_read_Single(self.config['boardIO']['_ADDRESS_TYPEC_IN_HOME_2_STATUS'])
        return True if not num else False

    def check_typec_in_test_2_status(self):
        num, data = self.innorev1_read_Single(self.config['boardIO']['_ADDRESS_TYPEC_IN_TEST_2_STATUS'])
        return True if not num else False

    def check_DUT_clamping_in_home_2_status(self):
        num, data = self.innorev1_read_Single(self.config['boardIO']['_ADDRESS_DUT_CLAMPING_IN_HOME_2_STATUS'])
        return True if not num else False

    def check_DUT_clamping_in_test_2_status(self):
        num, data = self.innorev1_read_Single(self.config['boardIO']['_ADDRESS_DUT_CLAMPING_IN_TEST_2_STATUS'])
        return True if not num else False

    def check_start_3_status(self):
        num, data = self.innorev1_read_Single(self.config['boardIO']['_ADDRESS_START_BUTTON_3_STATUS'])
        return True if not num else False

    def check_typec_in_home_3_status(self):
        num, data = self.innorev1_read_Single(self.config['boardIO']['_ADDRESS_TYPEC_IN_HOME_3_STATUS'])
        return True if not num else False

    def check_typec_in_test_3_status(self):
        num, data = self.innorev1_read_Single(self.config['boardIO']['_ADDRESS_TYPEC_IN_TEST_3_STATUS'])
        return True if not num else False

    def check_DUT_clamping_in_home_3_status(self):
        num, data = self.innorev1_read_Single(self.config['boardIO']['_ADDRESS_DUT_CLAMPING_IN_HOME_3_STATUS'])
        return True if not num else False

    def check_DUT_clamping_in_test_3_status(self):
        num, data = self.innorev1_read_Single(self.config['boardIO']['_ADDRESS_DUT_CLAMPING_IN_TEST_3_STATUS'])
        return True if not num else False

    # output
    def typec_control_1_open(self):
        s, data = self.innorev1.writeDO(self.config['boardIO']['_ADDRESS_TYPEC_1_CONTROL'], 0)
        return s

    def typec_control_1_close(self):
        s, data = self.innorev1.writeDO(self.config['boardIO']['_ADDRESS_TYPEC_1_CONTROL'], 1)
        return s

    def clamping_control_test_1_open(self):
        s, data = self.innorev1.writeDO(self.config['boardIO']['_ADDRESS_CLAMPING_TEST_1_CONTROL'], 0)
        return s

    def clamping_control_test_1_close(self):
        s, data = self.innorev1.writeDO(self.config['boardIO']['_ADDRESS_CLAMPING_TEST_1_CONTROL'], 1)
        return s

    def typec_control_2_open(self):
        s, data = self.innorev1.writeDO(self.config['boardIO']['_ADDRESS_TYPEC_2_CONTROL'], 0)
        return s

    def typec_control_2_close(self):
        s, data = self.innorev1.writeDO(self.config['boardIO']['_ADDRESS_TYPEC_2_CONTROL'], 1)
        return s

    def clamping_control_test_2_open(self):
        s, data = self.innorev1.writeDO(self.config['boardIO']['_ADDRESS_CLAMPING_TEST_2_CONTROL'], 0)
        return s

    def clamping_control_test_2_close(self):
        s, data = self.innorev1.writeDO(self.config['boardIO']['_ADDRESS_CLAMPING_TEST_2_CONTROL'], 1)
        return s

    def typec_control_3_open(self):
        s, data = self.innorev1.writeDO(self.config['boardIO']['_ADDRESS_TYPEC_3_CONTROL'], 0)
        return s

    def typec_control_3_close(self):
        s, data = self.innorev1.writeDO(self.config['boardIO']['_ADDRESS_TYPEC_3_CONTROL'], 1)
        return s

    def clamping_control_test_3_open(self):
        s, data = self.innorev1.writeDO(self.config['boardIO']['_ADDRESS_CLAMPING_TEST_3_CONTROL'], 0)
        return s

    def clamping_control_test_3_close(self):
        s, data = self.innorev1.writeDO(self.config['boardIO']['_ADDRESS_CLAMPING_TEST_3_CONTROL'], 1)
        return s

    def start_control_1_open(self):
        s, data = self.innorev1.writeDO(self.config['boardIO']['_ADDRESS_START_LIGHT_1_CONTROL'], 0)
        return s

    def start_control_1_close(self):
        s, data = self.innorev1.writeDO(self.config['boardIO']['_ADDRESS_START_LIGHT_1_CONTROL'], 1)
        return s

    def start_control_2_open(self):
        s, data = self.innorev1.writeDO(self.config['boardIO']['_ADDRESS_START_LIGHT_2_CONTROL'], 0)
        return s

    def start_control_2_close(self):
        s, data = self.innorev1.writeDO(self.config['boardIO']['_ADDRESS_START_LIGHT_2_CONTROL'], 1)
        return s

    def start_control_3_open(self):
        s, data = self.innorev1.writeDO(self.config['boardIO']['_ADDRESS_START_LIGHT_3_CONTROL'], 0)
        return s

    def start_control_3_close(self):
        s, data = self.innorev1.writeDO(self.config['boardIO']['_ADDRESS_START_LIGHT_3_CONTROL'], 1)
        return s

    def red_light_control_1_open(self):
        s, data = self.innorev1.writeDO(self.config['boardIO']['_ADDRESS_RED_LIGHT_1_CONTROL'], 0)
        return s

    def red_light_control_1_close(self):
        s, data = self.innorev1.writeDO(self.config['boardIO']['_ADDRESS_RED_LIGHT_1_CONTROL'], 1)
        return s

    def green_light_control_1_open(self):
        s, data = self.innorev1.writeDO(self.config['boardIO']['_ADDRESS_GREEN_LIGHT_1_CONTROL'], 0)
        return s

    def green_light_control_1_close(self):
        s, data = self.innorev1.writeDO(self.config['boardIO']['_ADDRESS_GREEN_LIGHT_1_CONTROL'], 1)
        return s

    def red_light_control_2_open(self):
        s, data = self.innorev1.writeDO(self.config['boardIO']['_ADDRESS_RED_LIGHT_2_CONTROL'], 0)
        return s

    def red_light_control_2_close(self):
        s, data = self.innorev1.writeDO(self.config['boardIO']['_ADDRESS_RED_LIGHT_2_CONTROL'], 1)
        return s

    def green_light_control_2_open(self):
        s, data = self.innorev1.writeDO(self.config['boardIO']['_ADDRESS_GREEN_LIGHT_2_CONTROL'], 0)
        return s

    def green_light_control_2_close(self):
        s, data = self.innorev1.writeDO(self.config['boardIO']['_ADDRESS_GREEN_LIGHT_2_CONTROL'], 1)
        return s

    def red_light_control_3_open(self):
        s, data = self.innorev1.writeDO(self.config['boardIO']['_ADDRESS_RED_LIGHT_3_CONTROL'], 0)
        return s

    def red_light_control_3_close(self):
        s, data = self.innorev1.writeDO(self.config['boardIO']['_ADDRESS_RED_LIGHT_3_CONTROL'], 1)
        return s

    def green_light_control_3_open(self):
        s, data = self.innorev1.writeDO(self.config['boardIO']['_ADDRESS_GREEN_LIGHT_3_CONTROL'], 0)
        return s

    def green_light_control_3_close(self):
        s, data = self.innorev1.writeDO(self.config['boardIO']['_ADDRESS_GREEN_LIGHT_3_CONTROL'], 1)
        return s

    # output 2
    def clamping_control_home_1_open(self):
        s, data = self.innorev2.writeDO(self.config['boardIO']['_ADDRESS_CLAMPING_HOME_1_CONTROL'], 0)
        return s

    def clamping_control_home_1_close(self):
        s, data = self.innorev2.writeDO(self.config['boardIO']['_ADDRESS_CLAMPING_HOME_1_CONTROL'], 1)
        return s

    def clamping_control_home_2_open(self):
        s, data = self.innorev2.writeDO(self.config['boardIO']['_ADDRESS_CLAMPING_HOME_2_CONTROL'], 0)
        return s

    def clamping_control_home_2_close(self):
        s, data = self.innorev2.writeDO(self.config['boardIO']['_ADDRESS_CLAMPING_HOME_2_CONTROL'], 1)
        return s

    def clamping_control_home_3_open(self):
        s, data = self.innorev2.writeDO(self.config['boardIO']['_ADDRESS_CLAMPING_HOME_3_CONTROL'], 0)
        return s

    def clamping_control_home_3_close(self):
        s, data = self.innorev2.writeDO(self.config['boardIO']['_ADDRESS_CLAMPING_HOME_3_CONTROL'], 1)
        return s

if __name__ == "__main__":
    dis = DisplayInterface()
    # print(dis.config['motor']['motor_disable'])
    # p rint(type(dis.config['motor']['motor_disable']))
    print(dis.clamping_1_test())
    print(dis.check_DUT_clamping_in_test_1_status())
