'''
Created on Aug 9, 2021

@author: liaoying
'''
'''
20210809  
1.initial version
'''
import serial.tools.list_ports
import platform
from datetime import datetime
import subprocess as sub
import yaml
import os, sys
import time
import threading


try:
    from FixtureControl.InnorevController import InnorevController
except:
    from InnorevController import InnorevController
    
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
        
        
class DisplayInterface_TurnTable(object):
    def __init__(self):
        self.innorev1 = None
        self.innorev2 = None
        self.config = None
        self._dut_1_index = 1
        self._dut_2_index = 2
        self.log = None
        self.log = Log(log_path)
        self._getConfigrution()
        self.connect()
        self.inside_dut_index = -1
        monitor_thread = threading.Thread(target=self.monitor_security_signal)
        monitor_thread1 = threading.Thread(target=self.monitor_reset_signal)
        monitor_thread.setDaemon(True)
        monitor_thread1.setDaemon(True)
        monitor_thread.start()
        monitor_thread1.start()
        print ('-----------------------')

    def monitor_reset_signal(self):
        self.is_rotate_out = True
        while True:
            try:
                if self.check_reset_button_status():
                    if self.open_door():
                        if self.is_rotate_out == True:
                            self.rotate_origin_control_open()
                            self.rotate_test_control_close()
                            self.is_rotate_out = False
                        else:
                            self.rotate_origin_control_close()
                            self.rotate_test_control_open()
                            self.is_rotate_out = True
                    else:
                        print ('Door is not opened')
                else:
                    time.sleep(.2)

            except Exception as ex:
                print (ex)
                time.sleep(.1)

        
    def init_control(self, index=1):
        self.is_testing = True
        self.inside_dut_index = -1
        msg = 'init control success'
        self.inside_dut_index = self.get_dut_inside_index()
        if -1 == self.inside_dut_index:
            msg = "Fail to get Inside dut (%s)" % str(self.inside_dut_index) 
            return False, msg
        if self.check_position_status(self.inside_dut_index):
            print ('There is a DUT inside.')
        else:
            self.log.write_log('begin to rotate')
            if self.open_door():
                if self.rotate_holder(self.inside_dut_index):
                    self.log.write_log('success to rotate')
                else:
                    msg = 'fail to rotate holder'
                    self.log.write_log(msg)
                    return False, msg
            else:
                msg = 'fail to open door'
                self.log.write_log(msg)
                return False, msg
        self.inside_dut_index = self.get_dut_inside_index()
        self.log.write_log ("test inside dut :" + str( self.inside_dut_index))
        ret, msg = self.typec_test(self.inside_dut_index)
        if ret:
            pass
        else:
            msg = 'fail to clamp dut (%s)' % str(self.inside_dut_index)
            self.log.write_log(msg)
            return False, msg

            
        if False == self.close_door():
            msg = 'fail to close door'
            self.log.write_log(msg)
            return False, msg

        return True, msg
    
    def cleanup_control(self, index=0):
        msg = 'cleanup control success'
        if self.open_door():
            self.log.write_log('open door success.')
            if self.rotate_holder(self.inside_dut_index):
                self.log.write_log('success to rotate.')
                ret, msg = self.typec_reset(self.inside_dut_index)
                if ret:
                    self.is_testing = False
                    pass
                else:
                    self.is_testing = False
                    return False, msg
            else:
                self.is_testing = False
                msg = 'fail to rotate holder.'
                self.log.write_log(msg)
                return False, msg
        else:
            self.is_testing = False
            msg = 'fail to open door.'
            self.log.write_log(msg)
            return False, msg
        self.is_testing = False
        return True, msg
    
    def rotate_holder(self, index):
        if self._dut_1_index == index:
            if self.rotate_test_control_close() and self.rotate_origin_control_open():
                number = 0
                while True:
                    number = number + 1
                    ret_3 = self.check_rotate_origin_status()
                    if ret_3:
                        self.log.write_log("rotate the holder to origin success")
                        return ret_3
                    if (number > 100):
                        self.log.write_log("rotate the holder to origin time out,ret_3{}".format(ret_3))
                        return ret_3
                    else:
                        time.sleep(0.1)
        else:
            if self.rotate_test_control_open() and self.rotate_origin_control_close():
                number = 0
                while True:
                    number = number + 1
                    ret_3 = self.check_rotate_test_status()
                    if ret_3:
                        self.log.write_log("rotate the holder to test success")
                        return ret_3
                    if (number > 100):
                        self.log.write_log("rotate the holder to test time out,ret_3{}".format(ret_3))
                        return ret_3
                    else:
                        time.sleep(0.1)
                        
    def close_door(self):
        if self.door_open_control_close() and self.door_close_control_open():
            number = 0
            while True:
                number = number + 1
                ret_3 = self.check_door_close_status()
                if ret_3:
                    self.log.write_log("close the door success")
                    return ret_3
                if (number > 100):
                    self.log.write_log("close the door time out,ret_3{}".format(ret_3))
                    return ret_3
                else:
                    time.sleep(0.1)
        
    
    def open_door(self):
        if self.door_open_control_open() and self.door_close_control_close():
            number = 0
            while True:
                number = number + 1
                ret_3 = self.check_door_open_status()
                if ret_3:
                    self.log.write_log("open the door success")
                    return ret_3
                if (number > 30):
                    self.log.write_log("open the door time out,ret_3{}".format(ret_3))
                    return ret_3
                else:
                    time.sleep(0.1)
    
    def typec_test(self, index):
        msg = 'typec test success'
        if self.insert_dut(index):
            self.log.write_log('success to insert dut (%s)' % str(index))
            return True, msg
        else:
            msg = 'fail to insert dut (%s)' % str(index)
            self.log.write_log(msg)
            return False, msg
            
    def typec_reset(self, index):
        msg = 'typec reset success'
        if self.release_dut(index):
            self.log.write_log('success to release dut (%s) typec' % str(index))
            return True, msg
        else:
            msg = 'fail to release dut (%s) typec' % str(index)
            self.log.write_log(msg)
            return False, msg
    
    def get_dut_inside_index(self):
        if self.check_rotate_test_status():
            return 1
        elif self.check_rotate_origin_status():
            return 2
        else:
            return -1
        
    def check_door_status(self):
        return True
    
    def OA_reset(self):
        return True

    def spin_move_to_test(self):
        return True

    def spin_move_to_home(self):
        return True

    def move_to_center(self):
        return True

    def move_to_down(self):
        return True
        
    def insert_dut(self, dut_number):
        if self._dut_1_index == dut_number:
            if self.dut1_typec_control_open():
                number = 0
                while True:
                    number = number + 1
                    ret_3 = self.check_typec1_test_status()
                    if ret_3:
                        self.log.write_log("insert dut1 typec success")
                        return ret_3
                    if (number > 30):
                        self.log.write_log("insert dut1 typec time out,ret_3{}".format(ret_3))
                        return ret_3
                    else:
                        time.sleep(0.1)
        else:
            print (self.dut2_typec_control_open())
            if self.dut2_typec_control_open():
                number = 0
                while True:
                    number = number + 1
                    ret_3 = self.check_typec2_test_status()
                    if ret_3:
                        self.log.write_log("insert dut2 typec success")
                        return ret_3
                    if (number > 30):
                        self.log.write_log("insert dut2 typec time out,ret_3{}".format(ret_3))
                        return ret_3
                    else:
                        time.sleep(0.1)
                        
    def release_dut(self, dut_number):
        if self._dut_1_index == dut_number:
            if self.dut1_typec_control_close():
                number = 0
                while True:
                    number = number + 1
                    ret_3 = self.check_typec1_origin_status()
                    if ret_3:
                        self.log.write_log("release dut1 typec success")
                        return ret_3
                    if (number > 30):
                        self.log.write_log("release dut1 typec time out,ret_3{}".format(ret_3))
                        return ret_3
                    else:
                        time.sleep(0.1)
        else:
            if self.dut2_typec_control_close():
                number = 0
                while True:
                    number = number + 1
                    ret_3 = self.check_typec2_origin_status()
                    if ret_3:
                        self.log.write_log("release dut2 typec success")
                        return ret_3
                    if (number > 30):
                        self.log.write_log("release dut2 typec time out,ret_3{}".format(ret_3))
                        return ret_3
                    else:
                        time.sleep(0.1)
        
    def check_position_status(self, dut_number):
        if self._dut_1_index == dut_number:
            return self.check_dut1_status()
        else:
            return self.check_dut2_status()
        
    def _getConfigrution(self):
        '''
        get yaml config
        '''
        with open(CONF_FILE_PATH, mode='r') as fp:
            print(CONF_FILE_PATH)
            config = yaml.safe_load(fp)
        config_path = config['config']['FATP-DISP-TurnTable']['config_path']
        # self.log = Log(config['config']['log_path'])
        self.log.write_log('config_path:{}'.format(config_path))
        if not os.path.exists(config_path):
            config_path = os.path.join(CURRENT_DIR, "displayTurnTable_config.yaml")
            print(config_path, "====1===")
            if not os.path.exists(config_path):
                raise Exception('Not find config file, please check')
        # else:
        with open(config_path, mode='r') as f:
            print(config_path)
            self.config = yaml.safe_load(f)

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
        
    def connect(self):
        lists = self.getSerials()
        print(lists)

        for port in lists:
            try:
                innorev = InnorevController(port.strip())
                if innorev.checkConnect():
                    print (innorev.ReadSN())
                    if innorev.ReadSN()[1] == '0001':
                        self.innorev1 = innorev
                        print("=============connect io card 1 success!=========%s" % port)
                        self.log.write_log("=============connect io card 1 success!=========%s" % port)
                    elif innorev.ReadSN()[1] == '0002':
                        self.innorev2 = innorev
                        print("=============connect io card2  success!=========%s" % port)
                        self.log.write_log("=============connect io card 2 success!=========%s" % port)
                    else:
                        innorev.close()
                else:
                    innorev.close()
                    continue
            except Exception as e:
                print(str(e))

    def monitor_security_signal(self):
        self.is_rotate_out = True
        while True:
            try:
                if self.check_saftey_curtain_status() == True:
                    pass
                else:
                    self.door_close_control_close()
                    self.door_open_control_close()
                    self.rotate_origin_control_close()
                    self.rotate_test_control_close()

            except Exception as ex:
                print (ex)
                time.sleep(.1)
            try:
                if self.check_emergency_stop_status() == True:
                    pass
                else:
                    self.door_close_control_close()
                    self.door_open_control_close()
                    self.rotate_origin_control_close()
                    self.rotate_test_control_close()
            except Exception as e:
                print(e)
                time.sleep(.1)
                
    def innorev_read_Single(self, io_ctrl, index):
        '''
        read io card single, if num == 'NAK', try again
        '''
        num, data = io_ctrl.readSingle(index)
        if num == True or num == False:
            return num, data
        else:
            number = 1
            while 1:
                num, data = io_ctrl.readSingle(index)
                if num == True or num == False:
                    print('+++++io card read again+++++')
                    self.log.write_log('+++++io card read again+++++')
                    return num, data
                elif number == 4:
                    raise Exception('read io card value error')
                self.log.write_log('====io card read again====read number: %s, num,data:%s %s' % (number, num, data))
                time.sleep(0.1)
                number += 1
    
    def check_emergency_stop_status(self):
        num, data = self.innorev_read_Single(self.innorev1, self.config['boardIO_1']['_ADDRESS_EMERGENCY_STOP_STATUS'])
        return True if not num else False

    def check_start_button_status(self):
        num, data = self.innorev_read_Single(self.innorev1, self.config['boardIO_1']['_ADDRESS_START_BUTTON_STATUS'])
        return True if not num else False

    def check_reset_button_status(self):
        num, data = self.innorev_read_Single(self.innorev1, self.config['boardIO_1']['_ADDRESS_RESET_BUTTON_STATUS'])
        return True if not num else False
    
    def check_saftey_curtain_status(self):
        num, data = self.innorev_read_Single(self.innorev1, self.config['boardIO_1']['_ADDRESS_SAFETY_CURTAIN_STATUS'])
        return True if not num else False
    
    def check_gas_source_status(self):
        num, data = self.innorev_read_Single(self.innorev1, self.config['boardIO_1']['_ADDRESS_GAS_CHECK_STATUS'])
        return True if not num else False
    
    def check_door_open_status(self):
        num, data = self.innorev_read_Single(self.innorev1, self.config['boardIO_1']['_ADDRESS_DOOR_OPEN_STATUS'])
        return True if not num else False
    
    def check_door_close_status(self):
        num, data = self.innorev_read_Single(self.innorev1, self.config['boardIO_1']['_ADDRESS_DOOR_CLOSE_STATUS'])
        return True if not num else False
    
    def check_rotate_origin_status(self):
        num, data = self.innorev_read_Single(self.innorev1, self.config['boardIO_1']['_ADDRESS_ROTATE_ORIGIN_STATUS'])
        return True if not num else False
    
    def check_rotate_test_status(self):
        num, data = self.innorev_read_Single(self.innorev1, self.config['boardIO_1']['_ADDRESS_ROTATE_TEST_STATUS'])
        return True if not num else False
    
    def start_control_open(self):
        s, data = self.innorev1.writeDO(self.config['boardIO_1']['_ADDRESS_START_BUTTON_CONTROL'], 0)
        return s
    
    def start_control_close(self):
        s, data = self.innorev1.writeDO(self.config['boardIO_1']['_ADDRESS_START_BUTTON_CONTROL'], 1)
        return s
    
    def reset_control_open(self):
        s, data = self.innorev1.writeDO(self.config['boardIO_1']['_ADDRESS_RESET_BUTTON_CONTROL'], 0)
        return s
    
    def reset_control_close(self):
        s, data = self.innorev1.writeDO(self.config['boardIO_1']['_ADDRESS_RESET_BUTTON_CONTROL'], 1)
        return s
    
    def red_light_control_open(self):
        s, data = self.innorev1.writeDO(self.config['boardIO_1']['_ADDRESS_RED_LIGHT_CONTROL'], 0)
        return s

    def red_light_control_close(self):
        s, data = self.innorev1.writeDO(self.config['boardIO_1']['_ADDRESS_RED_LIGHT_CONTROL'], 1)
        return s

    def green_light_control_open(self):
        s, data = self.innorev1.writeDO(self.config['boardIO_1']['_ADDRESS_GREEN_LIGHT_CONTROL'], 0)
        return s

    def green_light_control_close(self):
        s, data = self.innorev1.writeDO(self.config['boardIO_1']['_ADDRESS_GREEN_LIGHT_CONTROL'], 1)
        return s

    def door_close_control_open(self):
        s, data = self.innorev1.writeDO(self.config['boardIO_1']['_ADDRESS_DOOR_CLOSE_CONTROL'], 0)
        return s

    def door_close_control_close(self):
        s, data = self.innorev1.writeDO(self.config['boardIO_1']['_ADDRESS_DOOR_CLOSE_CONTROL'], 1)
        return s
    
    def door_open_control_open(self):
        s, data = self.innorev1.writeDO(self.config['boardIO_1']['_ADDRESS_DOOR_OPEN_CONTROL'], 0)
        return s

    def door_open_control_close(self):
        s, data = self.innorev1.writeDO(self.config['boardIO_1']['_ADDRESS_DOOR_OPEN_CONTROL'], 1)
        return s
    
    def rotate_origin_control_open(self):
        s, data = self.innorev1.writeDO(self.config['boardIO_1']['_ADDRESS_ROTATE_ORIGIN_CONTROL'], 0)
        return s

    def rotate_origin_control_close(self):
        s, data = self.innorev1.writeDO(self.config['boardIO_1']['_ADDRESS_ROTATE_ORIGIN_CONTROL'], 1)
        return s
    
    def rotate_test_control_open(self):
        s, data = self.innorev1.writeDO(self.config['boardIO_1']['_ADDRESS_ROTATE_TEST_CONTROL'], 0)
        return s

    def rotate_test_control_close(self):
        s, data = self.innorev1.writeDO(self.config['boardIO_1']['_ADDRESS_ROTATE_TEST_CONTROL'], 1)
        return s

    def check_typec1_test_status(self):
        num, data = self.innorev_read_Single(self.innorev2, self.config['boardIO_2']['_ADDRESS_TYPEC1_TEST_STATUS'])
        return True if not num else False
    
    def check_typec1_origin_status(self):
        num, data = self.innorev_read_Single(self.innorev2, self.config['boardIO_2']['_ADDRESS_TYPEC1_ORIGIN_STATUS'])
        return True if not num else False
    
    def check_dut1_status(self):
        num, data = self.innorev_read_Single(self.innorev2, self.config['boardIO_2']['_ADDRESS_DUT1_CHECK_STATUS'])
        return True if not num else False

    def check_typec2_test_status(self):
        num, data = self.innorev_read_Single(self.innorev2, self.config['boardIO_2']['_ADDRESS_TYPEC2_TEST_STATUS'])
        return True if not num else False
    
    def check_typec2_origin_status(self):
        num, data = self.innorev_read_Single(self.innorev2, self.config['boardIO_2']['_ADDRESS_TYPEC2_ORIGIN_STATUS'])
        return True if not num else False

    def check_dut2_status(self):
        num, data = self.innorev_read_Single(self.innorev2, self.config['boardIO_2']['_ADDRESS_DUT2_CHECK_STATUS'])
        return True if not num else False

    def dut1_typec_control_open(self):
        s, data = self.innorev2.writeDO(self.config['boardIO_2']['_ADDRESS_TYPEC1_INSERT_CONTROL'], 0)
        return s

    def dut1_typec_control_close(self):
        s, data = self.innorev2.writeDO(self.config['boardIO_2']['_ADDRESS_TYPEC1_INSERT_CONTROL'], 1)
        return s
    
    def dut2_typec_control_open(self):
        s, data = self.innorev2.writeDO(self.config['boardIO_2']['_ADDRESS_TYPEC2_INSERT_CONTROL'], 0)
        return s

    def dut2_typec_control_close(self):
        s, data = self.innorev2.writeDO(self.config['boardIO_2']['_ADDRESS_TYPEC2_INSERT_CONTROL'], 1)
        return s

if __name__ == '__main__':
    test = DisplayInterface_TurnTable()
    # print (test.get_dut_inside_index())
    test.init_control()
    time.sleep(5)
    test.cleanup_control()