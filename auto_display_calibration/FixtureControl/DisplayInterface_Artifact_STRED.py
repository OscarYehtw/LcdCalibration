# !/usr/bin/python
# -*- coding: UTF-8 -*-
'''
Created on 2020-10-09

@author: lzq
info: P7 DOE station
'''
'''v1.0.0.3      2021/03/26   @luzhiqiang
1.update start_control function typec_test() to clamp_test().
'''

'''v1.0.0.2      2021/01/29   @luzhiqiang
1.update start_control/init_control/cleanup_control function .
'''

'''v1.0.0.1      2020/12/28   @luzhiqiang
1.new API.
'''
VERSION = 'v1.0.0.2'

import serial.tools.list_ports
import platform
import time
from datetime import datetime
import subprocess as sub
import yaml
import os, sys
import datetime

from FixtureControl.InnorevController import InnorevController
import threading
from FixtureControl.innorev_6_channel_light_control import Innorev_Light_Cotrol
# from FixtureControl.ASDServoController import ASDServoController

log_path = os.path.join(os.path.expanduser('~'), 'Test_Log')

CURRENT_DIR = os.path.dirname(__file__)
print(CURRENT_DIR)
path = './displaycal_config.yaml'
print('1111111111111', os.path.exists(os.path.join(CURRENT_DIR, path)))
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

class DisplayInterface_Artifact_STRED(object):
    def __init__(self):
        self.innorev1 = None
        self.innorev2 = None
        self.light = None
        self.slot_index = -1
        self.asd = None
        self.config = None
        self._config_path = CONF_FILE_PATH
        self.log = None
        self.log = Log(log_path)
        self._getConfigrution()
        self.connect()
        self.reset()
        self.start_flag = True
        # self.start_lock = threading.Lock()
        self.start_thread = threading.Thread(target=self.start_control)
        self.start_thread.setDaemon(True)
        self.start_thread.start()

    def connect(self):
        lists = self.getSerials()
        print(lists)
        for port in lists:
            if "ttyS" not in port:
                print(port)
                try:
                    innorev = InnorevController(port.strip())
                    if innorev.checkConnect():
                        _, sn = innorev.ReadSN()
                        exec(f"self.innorev{int(sn)} = innorev")
                        print(f"=============connect io card {int(sn)} success!=========%s" % port)
                        self.log.write_log(f"=============connect io card {int(sn)} success!=========%s" % port)
                    else:
                        innorev.close()
                        continue
                except Exception as e:
                    print(str(e),"=============")

        for port in lists:
            try:
                self.light = Innorev_Light_Cotrol(port.strip())
                if self.light.checkConnect():
                    print ("=============connect Innorev_Light_Cotrol success!=========%s" % port)
                    self.log.write_log("=============connect Innorev_Light_Cotrol success!=========%s" % port)
                    self.light_flag = True
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
                if ("tty" in port):
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
        config_path = config['config']['FATP-DISP-ARTIFACT-STERD']['config_path']
        # self.log = Log(config['config']['log_path'])
        self.log.write_log('config_path:{}'.format(config_path))


        if not os.path.exists(config_path):
            config_path = os.path.join(CURRENT_DIR, "displayArtifact_STRED_config.yaml")
            print(config_path, "====1===")
            if not os.path.exists(config_path):
                raise Exception('Not find config file, please check')
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

    def get_DUT_port(self):
        port = None
        if self.slot_index == 1:
            port =  self.config['DUT_Port']['DUT_1']
        elif self.slot_index == 2:
            port = self.config['DUT_Port']['DUT_1']
        return port

    def start_control(self):
        while True:
            if self.start_flag:
                if self.check_start_button_status():
                    if self.check_holder_2_test_status():
                        # flag, msg = self.typec_1_test()
                        flag, msg = self.clamping_1_test()
                        if flag:
                            flag = self.holder_1_move_to_down()
                        if flag:
                            flag = self.holder_1_move_to_test()
                    elif self.check_holder_2_home_status():
                        # flag = self.typec_2_test()
                        flag = self.clamping_1_test()

            # if self.check_reset_button_status():
            #     if self.check_holder_2_test_status():
            #         self.typec_1_test()
            #         self.holder_1_move_to_down()
            #         self.holder_1_move_to_test()
            #
            #     elif self.check_holder_2_home_status():
            #         self.typec_2_test()
            time.sleep(0.5)

    def init_control(self, index=1):
        try:
            # self.start_lock.acquire()
            self.start_flag = False
            msg = 'Not DUT In Holder!'
            if self.check_holder_2_test_status():
                if self.check_DUT_2_position_status():
                    self.slot_index = 2
                    ret, msg = self.typec_2_test()
                    if ret:
                        ret, msg = self.door_move_to_test()
                    return ret, msg

                elif self.check_DUT_1_position_status():
                    ret, msg = self.typec_1_test()
                    if ret:
                        # ret, msg = self.holder_1_move_to_down()
                        ret, msg = self.door_move_to_home_holder_1_move_to_down()  # sync control
                    # if ret:
                    #     ret, msg = self.holder_1_move_to_test()
                    # if ret:
                    #     ret, msg = self.holder_2_move_to_home()
                    if ret:
                        ret, msg = self.holder_1_move_to_test_2_move_home()
                    if ret:
                        ret, msg = self.door_move_to_test_holder_1_move_to_up()  # sync control
                    #     ret, msg = self.holder_1_move_to_up()
                    # if ret:
                    #     ret, msg = self.door_move_to_test()
                    self.slot_index = 1
                    return ret, msg
                else:
                    self.slot_index = -1
                    return False, msg

    
            elif self.check_holder_2_home_status():
                if self.check_DUT_1_position_status():
                    self.slot_index = 1
                    ret, msg = self.typec_1_test()
                    if ret:
                        ret, msg = self.door_move_to_test()
                    return ret, msg

                elif self.check_DUT_2_position_status():
                    ret, msg = self.typec_2_test()
                    if ret:
                    #     ret, msg = self.holder_1_move_to_down()
                    # if ret:
                    #     ret, msg = self.door_move_to_home()
                        ret, msg = self.door_move_to_home_holder_1_move_to_down()  # sync control

                    # if ret:
                    #     ret, msg = self.holder_2_move_to_test()
                    #     ret, msg = True, ''
                    # if ret:
                    #     ret, msg = self.holder_1_move_to_home()
                    if ret:
                        ret, msg = self.holder_1_move_to_home_2_move_test()
                    if ret:
                        ret, msg = self.door_move_to_test_holder_1_move_to_up()  # sync control
                    #     ret, msg = self.holder_1_move_to_up()
                    # if ret:
                    #     ret, msg = self.door_move_to_test()
                    self.slot_index = 2
                    return ret, msg
                else:
                    self.slot_index = -1
                    return False, msg

            else:
                self.slot_index = -1
                return False, 'Holder 1 not sensor in position ,Please check sensor!'
        except Exception as e:
            print('init_control exception: ' , e)
            return False, e
        finally:
            self.start_flag = True
            # self.start_lock.release()


    def cleanup_control(self, index=1):
        try:
            # self.start_lock.acquire()
            self.slot_index = -1
            self.start_flag = False
            msg = ''
            print('self.check_holder_2_test_status()', self.check_holder_2_test_status())
            print('self.check_holder_2_home_status()', self.check_holder_2_home_status())
            if self.check_holder_2_test_status():

                if self.check_DUT_1_position_status():
                    ret, msg = self.typec_1_test()
                # ret, msg = self.door_move_to_home()
                # if ret:
                #     ret, msg = self.holder_1_move_to_down()
                ret, msg = self.door_move_to_home_holder_1_move_to_down()# sync control

                # if ret:
                #     ret, msg = self.holder_1_move_to_test()
                # if ret:
                #     ret, msg = self.holder_2_move_to_home()
                if ret:
                    ret, msg = self.holder_1_move_to_test_2_move_home()
                if ret:
                    # ret, msg = self.holder_1_move_to_up()
                    ret, msg = self.door_move_to_test_holder_1_move_to_up()# sync control

                if ret:
                    ret, msg = self.typec_2_release()
                self.start_flag = True
                return ret, msg
            elif self.check_holder_2_home_status():
                if self.check_DUT_2_position_status():
                    ret, msg = self.typec_2_test()
                # ret, msg = self.door_move_to_home()
                # if ret:
                #     ret, msg = self.holder_1_move_to_down()
                ret, msg = self.door_move_to_home_holder_1_move_to_down() # sync control

                # if ret:
                #     ret, msg = self.holder_1_move_to_home()
                # if ret:
                #     ret, msg = self.holder_2_move_to_test()
                if ret:
                    ret, msg = self.holder_1_move_to_home_2_move_test()
                if ret:
                    # ret, msg = self.holder_1_move_to_up()
                    ret, msg = self.door_move_to_test_holder_1_move_to_up()  # sync control
                if ret:
                    ret, msg = self.typec_1_release()
                self.start_flag = True
                return ret, msg
            else:
                return False, msg
        except Exception as e:
            print('cleanup_control exception:', e)
            self.log.write_log('cleanup_control exception: {}'.format(e))
            return False, msg
        finally:
            self.start_flag = True
            # self.start_lock.release()

    def reset(self):
        self.door_move_to_home()
        self.holder_1_move_to_down()
        self.holder_1_move_to_home_2_move_test()
        # self.holder_1_move_to_home()
        # self.holder_2_move_to_test()
        self.holder_1_move_to_up()
        self.typec_1_release()
        self.typec_2_release()
        return True

    # interface
    def get_version(self):
        global VERSION
        version = VERSION
        return version

    def door_move_to_test_holder_1_move_to_up(self):
        # self.door_move_to_test()
        # self.holder_1_move_to_up()

        self.holder_2_down_control_close()
        self.holder_2_up_control_open()
        self.door_control_home_close()
        self.door_control_test_open()

        number = 0
        while True:
            number = number + 1
            if not self.check_grating_status():
                self.log.write_log("satey grating_status result False ")
                print("satey grating_status result False ")
                self.holder_2_up_control_close()
                self.door_control_test_close()
            else:
                self.holder_2_up_control_open()
                self.door_control_test_open()

            door_ret = self.check_door_test_status()
            holder1_ret = self.check_holder_1_updown_test_status()
            if door_ret and holder1_ret:
                self.log.write_log("door_move_to_test and holder_1_move_to_up success")
                return True, ''
            if (number > 40):
                msg = "door_move_to_test or holder_1_move_to_up time out,door_ret {}, holder1_ret {}".format(door_ret, holder1_ret)
                self.log.write_log(msg)
                return False, msg
            else:
                time.sleep(0.1)

    def door_move_to_home_holder_1_move_to_down(self):
        # self.door_move_to_home()
        # self.holder_1_move_to_down()

        self.holder_2_down_control_open()
        self.holder_2_up_control_close()
        self.door_control_home_open()
        self.door_control_test_close()

        number = 0
        while True:
            number = number + 1
            if not self.check_grating_status():
                self.log.write_log("satey grating_status result False ")
                print("satey grating_status result False ")
                self.holder_2_down_control_close()
                self.door_control_home_close()
            else:
                self.holder_2_down_control_open()
                self.door_control_home_open()

            door_ret = self.check_door_home_status()
            holder1_ret = self.check_holder_1_updown_home_status()
            if door_ret and holder1_ret:
                self.log.write_log("door_move_to_home and holder_1_move_to_down success")
                return True, ''
            if (number > 40):
                msg = "door_move_to_home or holder_1_move_to_down time out,door_ret {}, holder1_ret {}".format(door_ret, holder1_ret)
                self.log.write_log(msg)
                return False, msg
            else:
                time.sleep(0.1)

    def holder_1_move_to_test_2_move_home(self):
        self.holder_1_test_control_open()
        self.holder_1_home_control_close()
        self.holder_2_test_control_close()
        self.holder_2_home_control_open()
        number = 0
        while True:
            number = number + 1
            if not self.check_grating_status():
                self.log.write_log("satey grating_status result False")
                self.holder_1_test_control_close()
                self.holder_2_home_control_close()
            else:
                self.holder_1_test_control_open()
                self.holder_2_home_control_open()


            ret1 = self.check_holder_1_test_status()
            ret2 = self.check_holder_2_home_status()
            if ret1 and ret2:
                self.log.write_log("holder_1_move_to_test_2_move_home success")
                return True, ''
            if (number > 30):
                msg = "holder_1_move_to_test time out,ret1{};2_move_home ret2 {}".format(ret1, ret2)
                self.log.write_log(msg)
                print(msg)
                return False, msg
            else:
                time.sleep(0.1)



    def holder_1_move_to_home_2_move_test(self):
        self.holder_1_test_control_close()
        self.holder_1_home_control_open()
        self.holder_2_test_control_open()
        self.holder_2_home_control_close()
        number = 0
        while True:
            number = number + 1
            if not self.check_grating_status():
                self.log.write_log("satey grating_status result False ")
                self.holder_1_home_control_close()
                self.holder_2_test_control_close()
            else:
                self.holder_1_home_control_open()
                self.holder_2_test_control_open()

            ret1 = self.check_holder_1_home_status()
            ret2 = self.check_holder_2_test_status()
            if ret1 and ret2:
                self.log.write_log("holder_1_move_to_home_2_move_test success")
                return True, ''
            if (number > 30):
                msg = "holder_1_move_to_home time out,ret1: {};2_move_test ret2: {}".format(ret1, ret2)
                self.log.write_log(msg)
                print(msg)
                return False, msg
            else:
                time.sleep(0.1)

    def holder_1_move_to_test(self):
        self.holder_1_test_control_open()
        self.holder_1_home_control_close()
        number = 0
        while True:
            number = number + 1
            ret = self.check_holder_1_test_status()
            if ret:
                self.log.write_log("holder_1_move_to_test success")
                return ret, ''
            if (number > 30):
                msg = "holder_1_move_to_test time out,ret{}".format(ret)
                self.log.write_log(msg)
                print(msg)
                return ret, msg
            else:
                time.sleep(0.1)

    def holder_1_move_to_home(self):
        self.holder_1_test_control_close()
        self.holder_1_home_control_open()
        number = 0
        while True:
            number = number + 1
            ret = self.check_holder_1_home_status()
            if ret:
                self.log.write_log("holder_1_move_to_home success")
                return ret, ''
            if (number > 30):
                msg = "holder_1_move_to_home time out, ret{}".format(ret)
                self.log.write_log(msg)
                print(msg)
                return ret, msg
            else:
                time.sleep(0.1)

    def holder_2_move_to_test(self):
        self.holder_2_test_control_open()
        self.holder_2_home_control_close()
        number = 0
        while True:
            number = number + 1
            ret = self.check_holder_2_test_status()
            if ret:
                self.log.write_log("holder_2_move_to_test success")
                return ret, ''
            if (number > 30):
                msg = "holder_2_move_to_test time out, ret {}".format(ret)
                self.log.write_log(msg)
                print(msg)
                return ret, msg
            else:
                time.sleep(0.1)

    def holder_2_move_to_home(self):
        self.holder_2_test_control_close()
        self.holder_2_home_control_open()
        number = 0
        while True:
            number = number + 1
            ret = self.check_holder_2_home_status()
            if ret:
                self.log.write_log("holder_2_move_to_home success")
                return ret, ''
            if (number > 30):
                msg = "holder_2_move_to_home time out, ret {}".format(ret)
                self.log.write_log(msg)
                print(msg)
                return ret, msg
            else:
                time.sleep(0.1)

    def holder_1_move_to_up(self):
        self.holder_2_down_control_close()
        self.holder_2_up_control_open()
        number = 0
        while True:
            number = number + 1
            if not self.check_grating_status():
                self.log.write_log("satey grating_status result False ")
                self.holder_2_up_control_close()
            else:
                self.holder_2_up_control_open()

            ret = self.check_holder_1_updown_test_status()
            if ret:
                self.log.write_log("holder_1_move_to_up success")
                return ret, ''
            if (number > 30):
                msg = "holder_1_move_to_up time out,ret{}".format(ret)
                self.log.write_log(msg)
                print(msg)
                return ret, msg
            else:
                time.sleep(0.1)

    def holder_1_move_to_down(self):
        self.holder_2_down_control_open()
        self.holder_2_up_control_close()
        number = 0
        while True:
            number = number + 1

            if not self.check_grating_status():
                self.log.write_log("satey grating_status result False ")
                self.holder_2_down_control_close()
            else:
                self.holder_2_down_control_open()

            ret = self.check_holder_1_updown_home_status()
            if ret:
                self.log.write_log("holder_1_move_to_down success")
                return ret, ''
            if (number > 30):
                msg = "holder_1_move_to_down time out,ret{}".format(ret)
                self.log.write_log(msg)
                print(msg)
                return ret, msg
            else:
                time.sleep(0.1)

    def door_move_to_home(self):
        self.door_control_home_open()
        self.door_control_test_close()
        number = 0
        while True:
            number = number + 1
            if not self.check_grating_status():
                self.log.write_log("satey grating_status result False ")
                print("satey grating_status result False ")
                self.door_control_home_close()
            else:
                self.door_control_home_open()

            ret = self.check_door_home_status()
            if ret:
                self.log.write_log("door_move_to_home success")
                return ret, ''
            if (number > 40):
                msg = "door_move_to_home time out,ret{}".format(ret)
                self.log.write_log(msg)
                return ret, msg
            else:
                time.sleep(0.1)

    def door_move_to_test(self):
        self.door_control_home_close()
        self.door_control_test_open()
        number = 0
        while True:
            number = number + 1
            if not self.check_grating_status():
                self.log.write_log("satey grating_status result False ")
                print("satey grating_status result False ")
                self.door_control_test_close()
                self.door_control_home_open()
            else:
                self.door_control_home_close()
                self.door_control_test_open()

            ret = self.check_door_test_status()
            if ret:
                self.log.write_log("door_move_to_test success")
                return ret, ''
            if (number > 40):
                msg = "door_move_to_test time out,ret{}".format(ret)
                self.log.write_log(msg)
                return ret, msg
            else:
                time.sleep(0.1)
    def typec_1_release(self):
        return self.typec_control_1_close() and self.clamping_control_1_close(), 'typec_1_release result'

    def typec_2_release(self):
        return self.typec_control_2_close() and self.clamping_control_2_close(), 'typec_2_release result'

    def typec_1_test(self):
        clamping_ret, msg = self.clamping_1_test()
        ret = False
        if clamping_ret:
            self.typec_control_1_open()
            number = 0
            while True:
                number = number + 1
                ret = self.check_typec_in_test_1_status()
                if ret:
                    self.log.write_log("typec 1 move to test success")
                    return ret, ''
                if (number > 30):
                    msg = "typec 1 move to test time out,ret{}".format(ret)
                    self.log.write_log(msg)
                    return ret, msg
                else:
                    time.sleep(0.1)
        return ret, msg

    def typec_2_test(self):
        clamping_ret, msg = self.clamping_2_test()
        ret = False
        if clamping_ret:
            self.typec_control_2_open()
            number = 0
            while True:
                number = number + 1
                ret = self.check_typec_in_test_2_status()
                if ret:
                    self.log.write_log("typec 2 move to test success")
                    return ret, msg
                if (number > 30):
                    msg = "typec 2 move to test time out,ret{}".format(ret)
                    self.log.write_log(msg)
                    return ret, msg
                else:
                    time.sleep(0.1)
        return ret, msg

    def clamping_1_test(self):
        if self.check_DUT_1_position_status() == False:
            return False
        else:
            self.clamping_control_1_open()
            number = 0
            while True:
                number = number + 1
                ret = self.check_DUT_clamping_in_test_1_status()
                if ret:
                    self.log.write_log("clamping 1 DUT to test success")
                    return ret, ''
                if (number > 30):
                    msg = "clamping 1 DUT to test time out,ret{}".format(ret)
                    self.log.write_log(msg)
                    return ret, msg
                else:
                    time.sleep(0.1)

    def clamping_2_test(self):
        if self.check_DUT_2_position_status() == False:
            return False
        else:
            self.clamping_control_2_open()
            number = 0
            while True:
                number = number + 1
                ret = self.check_DUT_clamping_in_test_2_status()
                if ret:
                    self.log.write_log("clamping 2 DUT to test success")
                    return ret, ''
                if (number > 30):
                    msg = "clamping 2 DUT to test time out,ret{}".format(ret)
                    self.log.write_log(msg)
                    return ret, msg
                else:
                    time.sleep(0.1)

    def light_open(self):
        channel = self.config['light_control']['channel']
        value = self.config['light_control']['value']
        ret = self.setbrightness(channel, value)
        return ret

    def light_close(self):
        channel = self.config['light_control']['channel']
        value = 0
        ret = self.setbrightness(channel, value)
        return ret

    def setbrightness(self, channel=1, value=500):
        ret = self.light.setBrightness(channel, value)
        return ret


    # input 1
    def check_emergency_stop_status(self):
        num, data = self.innorev1_read_Single(self.config['boardIO']['_ADDRESS_EMERGENCY_STOP_STATUS'])
        return True if not num else False

    def check_start_button_status(self):
        num, data = self.innorev1_read_Single(self.config['boardIO']['_ADDRESS_START_BUTTON_STATUS'])
        return True if not num else False

    def check_stop_button_status(self):
        num, data = self.innorev1_read_Single(self.config['boardIO']['_ADDRESS_STOP_BUTTON_STATUS'])
        return True if not num else False

    def check_reset_button_status(self):
        num, data = self.innorev1_read_Single(self.config['boardIO']['_ADDRESS_RESET_BUTTON_STATUS'])
        return True if not num else False

    def check_grating_status(self):
        num, data = self.innorev1_read_Single(self.config['boardIO']['_ADDRESS_GRATING_STATUS'])
        return True if not num else False

    def check_door_home_status(self):
        num, data = self.innorev2_read_Single(self.config['boardIO']['_ADDRESS_DOOR_HOME_STATUS'])
        return True if not num else False

    def check_door_test_status(self):
        num, data = self.innorev2_read_Single(self.config['boardIO']['_ADDRESS_DOOR_TEST_STATUS'])
        return True if not num else False

    def check_typec_in_home_1_status(self):
        num, data = self.innorev1_read_Single(self.config['boardIO']['_ADDRESS_TYPEC_1_HOME_STATUS'])
        return True if not num else False

    def check_typec_in_test_1_status(self):
        num, data = self.innorev1_read_Single(self.config['boardIO']['_ADDRESS_TYPEC_1_TEST_STATUS'])
        return True if not num else False

    def check_DUT_clamping_in_home_1_status(self):
        num, data = self.innorev1_read_Single(self.config['boardIO']['_ADDRESS_CLAMPING_1_HOME_STATUS'])
        return True if not num else False

    def check_DUT_clamping_in_test_1_status(self):
        num, data = self.innorev1_read_Single(self.config['boardIO']['_ADDRESS_CLAMPING_1_TEST_STATUS'])
        return True if not num else False

    def check_DUT_1_position_status(self):
        num, data = self.innorev1_read_Single(self.config['boardIO']['_ADDRESS_DUT_1_POSITION_STATUS'])
        return True if not num else False

    def check_holder_1_home_status(self):
        num, data = self.innorev1_read_Single(self.config['boardIO']['_ADDRESS_HOLDER_1_TRAN_HOME_STATUS'])
        return True if not num else False

    def check_holder_1_test_status(self):
        num, data = self.innorev1_read_Single(self.config['boardIO']['_ADDRESS_HOLDER_1_TRAN_TEST_STATUS'])
        return True if not num else False

    def check_holder_1_updown_home_status(self):
        num, data = self.innorev1_read_Single(self.config['boardIO']['_ADDRESS_HOLDER_1_UPDOWN_HOME_STATUS'])
        return True if not num else False

    def check_holder_1_updown_test_status(self):
        num, data = self.innorev1_read_Single(self.config['boardIO']['_ADDRESS_HOLDER_1_UPDOWN_TEST_STATUS'])
        return True if not num else False


    # input 2
    def check_typec_in_home_2_status(self):
        num, data = self.innorev2_read_Single(self.config['boardIO']['_ADDRESS_TYPEC_2_HOME_STATUS'])
        return True if not num else False

    def check_typec_in_test_2_status(self):
        num, data = self.innorev2_read_Single(self.config['boardIO']['_ADDRESS_TYPEC_2_TEST_STATUS'])
        return True if not num else False

    def check_DUT_clamping_in_home_2_status(self):
        num, data = self.innorev2_read_Single(self.config['boardIO']['_ADDRESS_CLAMPING_2_HOME_STATUS'])
        return True if not num else False

    def check_DUT_clamping_in_test_2_status(self):
        num, data = self.innorev2_read_Single(self.config['boardIO']['_ADDRESS_CLAMPING_2_TEST_STATUS'])
        return True if not num else False

    def check_DUT_2_position_status(self):
        num, data = self.innorev2_read_Single(self.config['boardIO']['_ADDRESS_DUT_2_POSITION_STATUS'])
        return True if not num else False

    def check_holder_2_home_status(self):
        num, data = self.innorev2_read_Single(self.config['boardIO']['_ADDRESS_HOLDER_2_TRAN_HOME_STATUS'])
        return True if not num else False

    def check_holder_2_test_status(self):
        num, data = self.innorev2_read_Single(self.config['boardIO']['_ADDRESS_HOLDER_2_TRAN_TEST_STATUS'])
        return True if not num else False

    # output 1
    def start_control_open(self):
        s, data = self.innorev1.writeDO(self.config['boardIO']['_ADDRESS_START_BUTTON_CONTROL'], 0)
        return s

    def start_control_close(self):
        s, data = self.innorev1.writeDO(self.config['boardIO']['_ADDRESS_START_BUTTON_CONTROL'], 1)
        return s

    def stop_control_open(self):
        s, data = self.innorev1.writeDO(self.config['boardIO']['_ADDRESS_STOP_BUTTON_CONTROL'], 0)
        return s

    def stop_control_close(self):
        s, data = self.innorev1.writeDO(self.config['boardIO']['_ADDRESS_STOP_BUTTON_CONTROL'], 1)
        return s

    def reset_control_open(self):
        s, data = self.innorev1.writeDO(self.config['boardIO']['_ADDRESS_RESET_BUTTON_CONTROL'], 0)
        return s

    def reset_control_close(self):
        s, data = self.innorev1.writeDO(self.config['boardIO']['_ADDRESS_RESET_BUTTON_CONTROL'], 1)
        return s

    def red_light_control_open(self):
        s, data = self.innorev1.writeDO(self.config['boardIO']['_ADDRESS_RED_LIGHT_CONTROL'], 0)
        return s

    def red_light_control_close(self):
        s, data = self.innorev1.writeDO(self.config['boardIO']['_ADDRESS_RED_LIGHT_CONTROL'], 1)
        return s

    def green_light_control_open(self):
        s, data = self.innorev1.writeDO(self.config['boardIO']['_ADDRESS_GREEN_LIGHT_CONTROL'], 0)
        return s

    def green_light_control_close(self):
        s, data = self.innorev1.writeDO(self.config['boardIO']['_ADDRESS_GREEN_LIGHT_CONTROL'], 1)
        return s

    def blue_light_control_open(self):
        s, data = self.innorev1.writeDO(self.config['boardIO']['_ADDRESS_BLUE_LIGHT_CONTROL'], 0)
        return s

    def blue_light_control_close(self):
        s, data = self.innorev1.writeDO(self.config['boardIO']['_ADDRESS_BLUE_LIGHT_CONTROL'], 1)
        return s

    def typec_control_1_open(self):
        s, data = self.innorev1.writeDO(self.config['boardIO']['_ADDRESS_TYPEC_1_CONTROL'], 0)
        return s

    def typec_control_1_close(self):
        s, data = self.innorev1.writeDO(self.config['boardIO']['_ADDRESS_TYPEC_1_CONTROL'], 1)
        return s

    def clamping_control_1_open(self):
        s, data = self.innorev1.writeDO(self.config['boardIO']['_ADDRESS_CLAMPING_1_CONTROL'], 0)
        return s

    def clamping_control_1_close(self):
        s, data = self.innorev1.writeDO(self.config['boardIO']['_ADDRESS_CLAMPING_1_CONTROL'], 1)
        return s

    def holder_2_up_control_open(self):
        s, data = self.innorev1.writeDO(self.config['boardIO']['_ADDRESS_HOLDER_1_UPDOWN_HOME_CONTROL'], 0)
        return s

    def holder_2_up_control_close(self):
        s, data = self.innorev1.writeDO(self.config['boardIO']['_ADDRESS_HOLDER_1_UPDOWN_HOME_CONTROL'], 1)
        return s

    def holder_2_down_control_open(self):
        s, data = self.innorev1.writeDO(self.config['boardIO']['_ADDRESS_HOLDER_1_UPDOWN_TEST_CONTROL'], 0)
        return s

    def holder_2_down_control_close(self):
        s, data = self.innorev1.writeDO(self.config['boardIO']['_ADDRESS_HOLDER_1_UPDOWN_TEST_CONTROL'], 1)
        return s

    def holder_1_test_control_open(self):
        s, data = self.innorev1.writeDO(self.config['boardIO']['_ADDRESS_HOLDER_1_TRAN_TEST_CONTROL'], 0)
        return s

    def holder_1_test_control_close(self):
        s, data = self.innorev1.writeDO(self.config['boardIO']['_ADDRESS_HOLDER_1_TRAN_TEST_CONTROL'], 1)
        return s

    def holder_1_home_control_open(self):
        s, data = self.innorev1.writeDO(self.config['boardIO']['_ADDRESS_HOLDER_1_TRAN_HOME_CONTROL'], 0)
        return s

    def holder_1_home_control_close(self):
        s, data = self.innorev1.writeDO(self.config['boardIO']['_ADDRESS_HOLDER_1_TRAN_HOME_CONTROL'], 1)
        return s



    # output 2
    def typec_control_2_open(self):
        s, data = self.innorev2.writeDO(self.config['boardIO']['_ADDRESS_TYPEC_2_CONTROL'], 0)
        return s

    def typec_control_2_close(self):
        s, data = self.innorev2.writeDO(self.config['boardIO']['_ADDRESS_TYPEC_2_CONTROL'], 1)
        return s

    def clamping_control_2_open(self):
        s, data = self.innorev2.writeDO(self.config['boardIO']['_ADDRESS_CLAMPING_2_CONTROL'], 0)
        return s

    def clamping_control_2_close(self):
        s, data = self.innorev2.writeDO(self.config['boardIO']['_ADDRESS_CLAMPING_2_CONTROL'], 1)
        return s

    def holder_2_home_control_open(self):
        s, data = self.innorev2.writeDO(self.config['boardIO']['_ADDRESS_HOLDER_2_TRAN_HOME_CONTROL'], 0)
        return s

    def holder_2_home_control_close(self):
        s, data = self.innorev2.writeDO(self.config['boardIO']['_ADDRESS_HOLDER_2_TRAN_HOME_CONTROL'], 1)
        return s

    def holder_2_test_control_open(self):
        s, data = self.innorev2.writeDO(self.config['boardIO']['_ADDRESS_HOLDER_2_TRAN_TEST_CONTROL'], 0)
        return s

    def holder_2_test_control_close(self):
        s, data = self.innorev2.writeDO(self.config['boardIO']['_ADDRESS_HOLDER_2_TRAN_TEST_CONTROL'], 1)
        return s

    def door_control_home_open(self):
        s, data = self.innorev2.writeDO(self.config['boardIO']['_ADDRESS_DOOR_HOME_CONTROL'], 0)
        return s

    def door_control_home_close(self):
        s, data = self.innorev2.writeDO(self.config['boardIO']['_ADDRESS_DOOR_HOME_CONTROL'], 1)
        return s

    def door_control_test_open(self):
        s, data = self.innorev2.writeDO(self.config['boardIO']['_ADDRESS_DOOR_TEST_CONTROL'], 0)
        return s

    def door_control_test_close(self):
        s, data = self.innorev2.writeDO(self.config['boardIO']['_ADDRESS_DOOR_TEST_CONTROL'], 1)
        return s


if __name__ == "__main__":
    dis = DisplayInterface_Artifact_STRED()
    i = 74817
    # from CanonControl import CanonControl
    exit()



    # capture_settings = {'iso': '1000', 'shutterspeed': '1/40', 'aperture': '16','imageformat':'Large Fine JPEG'}
    # canonCam.set_config_capture_save(capture_settings, './test_image.jpg')

    print("Running loop test")
    captureSetting = {"G127": {
        "iso": "1000",
        "aperture": "16",
        "shutterspeed": "1/10"
    }}

    while True:
        start_time = time.time()
        print(dis.init_control())

        if i % 100 == 0:
            canonCam = CanonControl()
            for config_name in ['eosserialnumber', 'iso', 'shutterspeed', 'aperture', 'imageformat']:
                print("Camera current config - {}: {}".format(config_name, canonCam.get_one_Config(config_name)))

            filename = '/home/innorev/Test_Log/picture/holder1/loop_%s.jpg' % i
            print('=======pygphoto2=====holder1/loop_%s.jpg' % i)
            canonCam.set_config_capture_save(captureSetting["G127"], filename)
            canonCam.__del__()

        if i % 100 == 1:
            canonCam = CanonControl()
            for config_name in ['eosserialnumber', 'iso', 'shutterspeed', 'aperture', 'imageformat']:
                print("Camera current config - {}: {}".format(config_name, canonCam.get_one_Config(config_name)))

            filename = '/home/innorev/Test_Log/picture/holder2/loop_%s.jpg' % i
            print('=======pygphoto2=====holder2/loop_%s.jpg' % i)
            canonCam.set_config_capture_save(captureSetting["G127"], filename)
            canonCam.__del__()

        print(dis.cleanup_control())
        print('=======number {}=======,===time {}====='.format(i, time.time() - start_time))
        dis.log.write_log('=======number {}=======,===time {}====='.format(i, time.time() - start_time))
        i += 1


    # start_time = time.time()
    # print(dis.init_control())
    # print(dis.cleanup_control())
    # print(time.time() - start_time)
    # start_time = time.time()
    # print(dis.door_move_to_test_holder_1_move_to_up())
    # print(time.time() - start_time)
    # time.sleep(2)
    # start_time = time.time()
    # print(dis.door_move_to_home_holder_1_move_to_down())
    # # print(dis.door_move_to_home())
    # # print(dis.cleanup_control())
    # print(time.time() - start_time)
    #
    #
    #
    # start_time = time.time()
    # print(dis.door_move_to_test_holder_1_move_to_up())
    # print(time.time() - start_time)

    # print(dis.init_control())
    # print(time.time() - start_time)
    # print(dis.holder_1_move_to_test_2_move_home())
    #
    # time.sleep(1)
    #
    # print(dis.holder_1_move_to_home_2_move_test())
    # print(dis.door_move_to_test())
    # time.sleep(1)
    # print(dis.door_move_to_home())

    # print(dis.holder_2_move_to_test())
    # time.sleep(1)
    # print(dis.holder_2_move_to_home())

    # print(dis.holder_1_move_to_test())
    # time.sleep(1)
    # print(dis.holder_1_move_to_home())

    # print(dis.holder_1_move_to_up())
    # time.sleep(1)
    # print(dis.holder_1_move_to_down())

    # print(dis.typec_2_test())
    # time.sleep(1)
    # print(dis.typec_2_release())

