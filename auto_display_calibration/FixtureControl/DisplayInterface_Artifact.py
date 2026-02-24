# !/usr/bin/python
# -*- coding: UTF-8 -*-
'''
Created on 2020-10-09

@author: lzq
'''

'''
20210325
1.add init_control() and cleanup_control() function.
2.update setbrightness() function insert (channel, value).
'''

'''
20210312
1.remove motor control.
2.remove move_to() function.
3.update reset() function remove move_to(0).
'''

'''
20210204 
1.update connect CPL control.
2.update import  controller.

'''


'''
20201124 
1.remove light_disable key.
2.remove reset funtion light close.
'''

'''
20201121 
1.add light_disable key.
'''

'''
20201114 change opt control.
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
    from FixtureControl.MoonsController import MoonsController
    from FixtureControl.CPLController import CPLController
    from FixtureControl.OptLightController import OptLightController
except:
    from InnorevController import InnorevController
    from ASDServoController import ASDServoController
    from MoonsController import MoonsController
    from CPLController import CPLController
    from OptLightController import OptLightController

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

class DisplayInterface_Artifact(object):
    def __init__(self):
        self.innorev = None
        self.config = None
        self._config_path = CONF_FILE_PATH
        self.log = None
        self.log = Log(log_path)
        self._getConfigrution()
        self.connect()
        self.reset()

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
                    lists.remove(port)
                else:
                    innorev.close()
                    continue
            except Exception as e:
                print(str(e))

        light_list = []
        light_list.append('/dev/ttyS0')
        light_list.append('/dev/ttyS1')
        for port in light_list:
            try:
                self.light = CPLController(port.strip())
                if self.light.checkConnect():
                    print ("=============connect CPLController success!=========%s" % port)
                    self.log.write_log("=============connect CPLController success!=========%s" % port)
                    break
                else:
                    self.light.close()
                    continue
            except (Exception)as e:
                print (str(e))

            try:
                self.light = OptLightController(port.strip())
                if self.light.checkConnect():
                    print ("=============connect OptController success!=========%s" % port)
                    self.log.write_log("=============connect OptController success!=========%s" % port)
                    break
                else:
                    self.light.close()
                    continue
            except (Exception)as e:
                print (str(e))

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
        config_path = config['config']['FATP-DISP-ARTIFACT']['config_path']
        # self.log = Log(config['config']['log_path'])
        self.log.write_log('config_path:{}'.format(config_path))
        if not os.path.exists(config_path):
            config_path = os.path.join(CURRENT_DIR, "displayArtifact_config.yaml")
            print(config_path, "====1===")
            if not os.path.exists(config_path):
                raise Exception('Not find config file, please check')
        # else:
        with open(config_path, mode='r') as f:
            print(config_path)
            self.config = yaml.safe_load(f)

    def innorev_read_Single(self, index):
        '''
        read io card single, if num == 'NAK', try again
        '''
        num, data = self.innorev.readSingle(index)
        if num == True or num == False:
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
    #interface
    # check_DUT_position_status() position sensor

    def init_control(self, index=1):
        msg = 'init control success'
        ret = self.check_DUT_position_status()
        if not ret:
            msg = 'Check fixture door - Pass?  {}'.format(ret)
            return ret, msg
        ret = self.typec_test()
        if not ret:
            msg = 'Clamp unit and insert USB - Pass? {}'.format(ret)
            return ret, msg

        return ret, msg

    def cleanup_control(self, index=1):
        return self.typec_reset(), ''

    def reset(self):
        self.typec_reset()

    def light_open(self):
        channel = self.config["light_config"]["channel"]
        value = self.config["light_config"]["value"]
        ret = self.setbrightness(channel, value)
        return ret

    def light_close(self):
        channel = self.config["light_config"]["channel"]
        value = 0
        ret = self.setbrightness(channel, value)
        return ret

    def setbrightness(self, channel=0, value=100):
        ret = self.light.setBrightness(channel, value)
        return ret

    def typec_reset(self):
        typec_ret_1 = self.typec_control_close()
        clamping_ret_1 = self.clamping_control_close()
        self.log.write_log("reset result:typec:{}; clamping:{}".
                           format(typec_ret_1, clamping_ret_1))
        return typec_ret_1 and clamping_ret_1

    def typec_test(self):
        clamping_ret = self.clamping_test()
        ret = False
        if clamping_ret:
            self.typec_control_open()
            number = 0
            while True:
                number = number + 1
                ret = self.check_typec_test_status()
                if ret:
                    self.log.write_log("typec to test success")
                    return ret
                if (number > 30):
                    self.log.write_log("typec to test time out,ret{}".format(ret))
                    return ret
                else:
                    time.sleep(0.1)
        return ret

    def clamping_test(self):
        self.clamping_control_open()
        number = 0
        while True:
            number = number + 1
            ret = self.check_clamping_test_status()
            if ret:
                self.log.write_log("clamping DUT to test success")
                return ret
            if (number > 30):
                self.log.write_log("clamping DUT to test time out,ret{}".format(ret))
                return ret
            else:
                time.sleep(0.1)

    # input
    def check_emergency_stop_status(self):
        num, data = self.innorev_read_Single(self.config['boardIO']['_ADDRESS_EMERGENCY_STOP_STATUS'])
        return True if not num else False

    def check_start_button_status(self):
        num, data = self.innorev_read_Single(self.config['boardIO']['_ADDRESS_START_BUTTON_STATUS'])
        return True if not num else False

    def check_stop_button_status(self):
        num, data = self.innorev_read_Single(self.config['boardIO']['_ADDRESS_STOP_BUTTON_STATUS'])
        return True if not num else False

    def check_reset_button_status(self):
        num, data = self.innorev_read_Single(self.config['boardIO']['_ADDRESS_RESET_BUTTON_STATUS'])
        return True if not num else False


    def check_typec_home_status(self):
        num, data = self.innorev_read_Single(self.config['boardIO']['_ADDRESS_TYPEC_HOME_STATUS'])
        return True if not num else False

    def check_typec_test_status(self):
        num, data = self.innorev_read_Single(self.config['boardIO']['_ADDRESS_TYPEC_TEST_STATUS'])
        return True if not num else False

    def check_clamping_home_status(self):
        num, data = self.innorev_read_Single(self.config['boardIO']['_ADDRESS_CLAMPING_HOME_STATUS'])
        return True if not num else False

    def check_clamping_test_status(self):
        num, data = self.innorev_read_Single(self.config['boardIO']['_ADDRESS_CLAMPING_TEST_STATUS'])
        return True if not num else False

    def check_DUT_position_status(self):
        num, data = self.innorev_read_Single(self.config['boardIO']['_ADDRESS_DUT_POSITION_STATUS'])
        return True if not num else False

    # output
    def typec_control_open(self):
        s, data = self.innorev.writeDO(self.config['boardIO']['_ADDRESS_TYPEC_CONTROL'], 0)
        return s

    def typec_control_close(self):
        s, data = self.innorev.writeDO(self.config['boardIO']['_ADDRESS_TYPEC_CONTROL'], 1)
        return s

    def clamping_control_open(self):
        s, data = self.innorev.writeDO(self.config['boardIO']['_ADDRESS_CLAMPING_CONTROL'], 0)
        return s

    def clamping_control_close(self):
        s, data = self.innorev.writeDO(self.config['boardIO']['_ADDRESS_CLAMPING_CONTROL'], 1)
        return s

    def start_control_open(self):
        s, data = self.innorev.writeDO(self.config['boardIO']['_ADDRESS_START_BUTTON_CONTROL'], 0)
        return s

    def start_control_close(self):
        s, data = self.innorev.writeDO(self.config['boardIO']['_ADDRESS_START_BUTTON_CONTROL'], 1)
        return s

    def stop_control_open(self):
        s, data = self.innorev.writeDO(self.config['boardIO']['_ADDRESS_STOP_BUTTON_CONTROL'], 0)
        return s

    def stop_control_close(self):
        s, data = self.innorev.writeDO(self.config['boardIO']['_ADDRESS_STOP_BUTTON_CONTROL'], 1)
        return s

    def reset_control_open(self):
        s, data = self.innorev.writeDO(self.config['boardIO']['_ADDRESS_RESET_BUTTON_CONTROL'], 0)
        return s

    def reset_control_close(self):
        s, data = self.innorev.writeDO(self.config['boardIO']['_ADDRESS_RESET_BUTTON_CONTROL'], 1)
        return s

    def red_light_control_open(self):
        s, data = self.innorev.writeDO(self.config['boardIO']['_ADDRESS_RED_LIGHT_CONTROL'], 0)
        return s

    def red_light_control_close(self):
        s, data = self.innorev.writeDO(self.config['boardIO']['_ADDRESS_RED_LIGHT_CONTROL'], 1)
        return s

    def green_light_control_open(self):
        s, data = self.innorev.writeDO(self.config['boardIO']['_ADDRESS_GREEN_LIGHT_CONTROL'], 0)
        return s

    def green_light_control_close(self):
        s, data = self.innorev.writeDO(self.config['boardIO']['_ADDRESS_GREEN_LIGHT_CONTROL'], 1)
        return s

    def blue_light_control_open(self):
        s, data = self.innorev.writeDO(self.config['boardIO']['_ADDRESS_BLUE_LIGHT_CONTROL'], 0)
        return s

    def blue_light_control_close(self):
        s, data = self.innorev.writeDO(self.config['boardIO']['_ADDRESS_BLUE_LIGHT_CONTROL'], 1)
        return s
    

if __name__ == "__main__":
    displayinterface = DisplayInterface_Artifact()
    displayinterface.typec_test()
    time.sleep(1)
    displayinterface.typec_reset()

    displayinterface.light_open()
