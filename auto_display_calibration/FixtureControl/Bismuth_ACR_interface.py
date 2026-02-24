# !/usr/bin/python
# -*- coding: UTF-8 -*-
import serial.tools.list_ports
import platform
import time
from datetime import datetime
import subprocess as sub
import yaml
import os, sys
import datetime
from InnorevController import InnorevController
import CL200A
from CSTLight_control import CSTLight



log_path = os.path.join(os.path.expanduser('~'), 'Test_Log')


class Log(object):
    def __init__(self, filename='./log'):
        self.filename = filename

    def write_log(self, message):
        path = self.filename
        if os.path.exists(path) == False:
            os.makedirs(path)
        strtime = time.strftime("%Y-%m-%d", time.localtime())
        log_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        filename = path + '/' + strtime + '.txt'
        # print (filename)
        fp = open(filename, 'ab')
        log = log_time + ':' + str(message)
        log = log.encode('unicode-escape')
        fp.write(log + b'\r\n')
        fp.close()


class Bismuth_ACR_interface (object):
    def __init__(self):
        self.innorev1 = None
        self.innorev2 = None
        self.config = None

        self.log = None
        self.log = Log()
        self._getConfigrution()
        self.io_flag = False
        self.asd_flag = False
        self.light_flag = False
        self.connect()

    def _getConfigrution(self):
        config_path = './FixtureControl/Configuration.yaml'
        # self.log.write_log('config_path:{}'.format(config_path))
        if not os.path.exists(config_path):
            raise Exception('Not find config file, please check')
        else:
            with open(config_path, mode='r') as f:
                print(config_path)
                self.config = yaml.safe_load(f)

    def connect(self):
        lists = self.getSerials()
        print("---------", lists)
        for port in lists:
            try:
                innorev = InnorevController(port.strip())
                if innorev.checkConnect():
                    _, id = innorev.ReadSN()
                    if "0001" in id:
                        self.innorev1 = innorev
                        print("=============connect io card1  success!=========%s" % port)
                        self.log.write_log("=============connect io card1  success!=========%s" % port)
                        self.io_flag = True
                        lists.remove(port)

                else:
                    innorev.close()
                    continue
            except Exception as e:
                print(str(e))


        light_list = self.getSerials()

        cl200aflag = False
        for port in light_list:
            try:
                self.cl200a = CL200A.CL200AController(port.strip())
                if self.cl200a.checkConnect():
                    cl200aflag = True
                    print("=============connect cl200a success!=========", port)
                    light_list.remove(port)
                    break
                else:
                    self.cl200a.close()
                    continue
            except Exception as e:
                # print str(e)
                pass
        if cl200aflag == False:
            print('CL200A port fail')
        arr_led_T=False
        self.light = None
        ListLight=['/dev/ttyS0', '/dev/ttyS1']
        for arr_port in ListLight:
            try:
                arr_led_T = True
                self.light = CSTLight(arr_port)
                if self.light.checkConnect():
                    print("=============connect led success!=========", arr_port)
                    break
                else:
                    continue
            except Exception as e:
                print(str(e))
                pass
        if arr_led_T == False:
            print('led port fail')
        # self.reset()
    def getSerials(self):
        port_list = serial.tools.list_ports.comports()
        lists = list()
        system = platform.system()
        if (system == "Linux"):
            for port in port_list:
                port = str(port.device)
                if ("USB" in port):
                    lists.append(port)
                if ("ttyS" in port):
                    lists.append(port)
        elif system == "Darwin":

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


    def read_DI(self, di_address):
        if self.innorev1 is not None:
            return self.innorev1.readSingle(di_address)[0]
        return 0

    def readAllDI_label(self):

        self.DI_Status_label_list = ['label_E_Stop',
                                     'label_Start_Button',
                                     'label_RESET_Button',
                                     'label_Stop_Button',
                                     'label_Door',
                                     'label_CHECK_DUT',
                                     'label_Typec_ORIGIN',
                                     'label_Typec_Test',
                                     ]
        return [
            self.read_DI(self.config['boardIO1']['input']['E_Stop']),
            self.read_DI(self.config['boardIO1']['input']['START_STATUS']),
            self.read_DI(self.config['boardIO1']['input']['RESET_STATUS']),
            self.read_DI(self.config['boardIO1']['input']['STOP_STATUS']),
            self.read_DI(self.config['boardIO1']['input']['DOOR_STATUS']),
            self.read_DI(self.config['boardIO1']['input']['HOLD_STATUS']),
            self.read_DI(self.config['boardIO1']['input']['TYPEC_ORIGIN']),
            self.read_DI(self.config['boardIO1']['input']['TYPEC_TEST']),
        ]


    def read_DI_Button(self, di_address):
        if self.innorev1 is not None:
            return self.innorev1.readSingle(di_address,1)[0]
        return 0

    def readAllDI_Button(self):

        self.DI_Status_Button_list = ['pushButton_Start_Button',
                                      'pushButton_RESET_Button',
                                      'pushButton_Stop_Button',

                                      'pushButton_Two_light_Red',
                                      'pushButton_Two_light_Greed',
                                      'pushButton_Typec',
                                     ]
        return [
            self.read_DI_Button(self.config['boardIO1']['output']['START_LIGHT']),
            self.read_DI_Button(self.config['boardIO1']['output']['RESET_LIGHT']),
            self.read_DI_Button(self.config['boardIO1']['output']['STOP_LIGHT']),
            self.read_DI_Button(self.config['boardIO1']['output']['TWO_COLOR_GREEN']),
            self.read_DI_Button(self.config['boardIO1']['output']['TWO_COLOR_RED']),
            self.read_DI_Button(self.config['boardIO1']['output']['TYPEC']),
        ]


    def check_E_Stop(self):
        num, data = self.innorev1.readSingle(self.config['boardIO1']['input']['E_Stop'])
        return True if not num else False

    def check_START_STATUS(self):
        num, data = self.innorev1.readSingle(self.config['boardIO1']['input']['START_STATUS'])
        return True if not num else False

    def check_RESET_STATUS(self):
        num, data = self.innorev1.readSingle(self.config['boardIO1']['input']['RESET_STATUS'])
        return True if not num else False

    def check_STOP_STATUS(self):
        num, data = self.innorev1.readSingle(self.config['boardIO1']['input']['STOP_STATUS'])
        return True if not num else False

    def check_DOOR_STATUS(self):
        num, data = self.innorev1.readSingle(self.config['boardIO1']['input']['DOOR_STATUS'])
        return True if not num else False

    def check_HOLD_STATUS(self):
        num, data = self.innorev1.readSingle(self.config['boardIO1']['input']['HOLD_STATUS'])
        return True if not num else False

    def check_TYPEC_ORIGIN(self):
        num, data = self.innorev1.readSingle(self.config['boardIO1']['input']['TYPEC_ORIGIN'])
        return True if not num else False

    def check_TYPEC_TEST(self):
        num, data = self.innorev1.readSingle(self.config['boardIO1']['input']['TYPEC_TEST'])
        return True if not num else False

    def START_LIGHT_open(self):
        s, data = self.innorev1.writeDO(self.config['boardIO1']['output']['START_LIGHT'], 0)
        return s

    def START_LIGHT_off(self):
        s, data = self.innorev1.writeDO(self.config['boardIO1']['output']['START_LIGHT'], 1)
        return s

    def RESET_LIGHT_open(self):
        s, data = self.innorev1.writeDO(self.config['boardIO1']['output']['RESET_LIGHT'], 0)
        return s

    def RESET_LIGHT_off(self):
        s, data = self.innorev1.writeDO(self.config['boardIO1']['output']['RESET_LIGHT'], 1)
        return s

    def STOP_LIGHT_open(self):
        s, data = self.innorev1.writeDO(self.config['boardIO1']['output']['STOP_LIGHT'], 0)
        return s

    def STOP_LIGHT_off(self):
        s, data = self.innorev1.writeDO(self.config['boardIO1']['output']['STOP_LIGHT'], 1)
        return s

    def TWO_COLOR_GREEN_open(self):
        s, data = self.innorev1.writeDO(self.config['boardIO1']['output']['TWO_COLOR_GREEN'], 0)
        return s

    def TWO_COLOR_GREEN_off(self):
        s, data = self.innorev1.writeDO(self.config['boardIO1']['output']['TWO_COLOR_GREEN'], 1)
        return s

    def TWO_COLOR_RED_open(self):
        s, data = self.innorev1.writeDO(self.config['boardIO1']['output']['TWO_COLOR_RED'], 0)
        return s

    def TWO_COLOR_RED_off(self):
        s, data = self.innorev1.writeDO(self.config['boardIO1']['output']['TWO_COLOR_RED'], 1)
        return s

    def TYPEC_open(self):
        s, data = self.innorev1.writeDO(self.config['boardIO1']['output']['TYPEC'], 0)
        return s

    def TYPEC_off(self):
        s, data = self.innorev1.writeDO(self.config['boardIO1']['output']['TYPEC'], 1)
        return s


   # 按配文件开灯
    def light_open(self):
        channel = self.config["light_config"]["channel"]
        value = self.config["light_config"]["value"]
        ret = self.setbrightness(channel, value)
        return ret

    # 按配文件关灯
    def light_close(self):
        channel = self.config["light_config"]["channel"]
        value = 0
        ret = self.setbrightness(channel, value)
        return ret

    # 按参数开灯
    def setbrightness(self, channel=0, value=100):
        ret = self.light.set_Brightness(channel, value)
        return ret
    #读取照度计值
    def cl200a_read(self):
        flag,current_illuminance ,current_CCT,delta_uv_value=self.cl200a.read()
        return  flag,current_illuminance ,current_CCT,delta_uv_value

    # 读取照度计值
    def cl200a_read_XYZ(self):
        flag, X, Y, Z = self.cl200a.read_XYZ()
        return flag, X, Y, Z

    # 读取照度计值
    def cl200a_read_Evxy(self):
        flag, Ev, x, y = self.cl200a.read_Evxy()
        return flag, Ev, x, y

    # 插入typec,并判断到位
    def insert_typec(self, check_time=5):
        """
        insert_typec
        :param check_time:检测超时时间，单位：秒
        :return:true/false, msg
        """
        try:

            if self.check_E_Stop() == False:
                return False, " check E_Stop "

            self.TYPEC_open()
            start_time = time.time()
            while ((time.time() - start_time) < check_time):
                if (self.check_TYPEC_TEST()):
                    return True, "Success to insert typec"
            return False, "Fail to insert typec"
        except Exception as ex:
            return False, "Raise exception(%s)" % str(ex)



    # 拔出typec,并判断到位
    def release_typec(self, check_time=5):
        """
        insert_typec
        :param check_time:检测超时时间，单位：秒
        :return:true/false, msg
        """
        try:
            if self.check_E_Stop() == False:
                return False, " check E_Stop "

            self.TYPEC_off()
            start_time = time.time()
            while ((time.time() - start_time) < check_time):
                if (self.check_TYPEC_ORIGIN()):
                    return True, "Success to release  typec"
            return False, "Fail to release  typec"
        except Exception as ex:
            return False, "Raise exception(%s)" % str(ex)


    def init_control(self, index):
        msg = 'Init control success'
        ret = self.check_position_status(index)
        if not ret:
            msg = 'DUT not in Holder1 cover'
            return ret, msg
        ret = self.typec_test(index)
        if not ret:
            msg = 'Typec insert issue'
            return ret, msg
        return ret, msg
    def check_position_status(self, index):
        return self.check_HOLD_STATUS()
    def typec_test(self, index):
        return self.insert_typec()[0]

    def cleanup_control(self, index):
        msg = 'cleanup control success'
        ret = self.typec_reset(index)
        if not ret:
            msg = 'cleanup control fail'
            return ret, msg
        return ret, msg

    def typec_reset(self, index):
        return self.release_typec()[0]

    def check_door_status(self):
        return self.check_DOOR_STATUS()

if __name__ == "__main__":
    displayinterface = Bismuth_ACR_interface()
    displayinterface.insert_typec()


