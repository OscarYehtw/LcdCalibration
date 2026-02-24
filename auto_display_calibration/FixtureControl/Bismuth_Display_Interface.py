# -*- coding: utf-8 -*-

import time
from InnorevFramework.Common.Iinterface import Iinterface,InterfaceBuild
from InnorevFramework.Common import Common, AppConfigHelper
from InnorevFramework.Common.Config import ConfiIni
from InnorevFramework.FixtureControl.IOController import *
from InnorevFramework.FixtureControl.CPLController import *
import os, json
# import pygame

SFR_IO1_CONFIG_NAME = "IOConfig_1"
# SFR_IO2_CONFIG_NAME = "IOConfig_2"
SFR_CONFIG_NAME = "Display_Configuration"


ON = 0
OFF = 1


class Display_Interface(Iinterface):
    def __init__(self):
        try:
            super(type(self), self).__init__(None)
            self.ioconfig1_file = Common.findFile(AppConfigHelper.get_config_directory(), SFR_IO1_CONFIG_NAME)
            # self.ioconfig2_file = Common.findFile(AppConfigHelper.get_config_directory(), SFR_IO2_CONFIG_NAME)
            self.hmdconfig_file = Common.findFile(AppConfigHelper.get_config_directory(), SFR_CONFIG_NAME)

            # print (self.hmdconfig_file)
            # print (self.ioconfig1_file, self.ioconfig2_file)

            self.hmdconfig_1 = ConfiIni(self.hmdconfig_file)           # 位置等参数配置
            self.ioconfig_1 = ConfiIni(self.ioconfig1_file)             # io 配置

            # self.hmdconfig_2 = ConfiIni(self.hmdconfig_file)
            # self.ioconfig_2 = ConfiIni(self.ioconfig2_file)
            # print (self._io_file)

        except Exception as ex:
            print (str(ex))

        try:
            print("----------------------",self.hmdconfig_1.get('coms', "io_port"))
            print("----------------------", self.ioconfig1_file)
            self.io_ctrl_1 = IOController(self.hmdconfig_1.get('coms', "io_port"), io_file_name= self.ioconfig1_file)
        except Exception as ex:
            print (str(ex))

        self.init()

        # try:
        #     self.io_ctrl_2 = IOController(self.hmdconfig_2.get('coms', "io2_port"), io_file_name=self.ioconfig2_file)
        # except Exception as ex:
        #     print (str(ex))

    def init(self):
        """
        初始化
        :return:
        """
        ports = Common.getports()
        print (ports)

        status, port, msg = self.io_ctrl_1.checkconnect(ports)
        print (status, port, msg)
        if status is True:
            result, msg = self.io_ctrl_1.ReadID()
            if result == True and msg == 1:
                self.hmdconfig_1.set_value("coms", "io1_port", port)
                self.hmdconfig_1.save()
            ports.remove(port)
        else:
            pass

        # status, port, msg = self.io_ctrl_2.checkconnect(ports)
        # print (status, port, msg)
        # if status is True:
        #     result, msg = self.io_ctrl_2.ReadID()
        #     if result == True and msg == 2:
        #         self.hmdconfig_2.set_value("coms", "io2_port", port)
        #         self.hmdconfig_2.save()
        # else:
        #     pass

    @InterfaceBuild("Display_Interface", "typec1_test", u"insert typec_1 测试", "typec_1_test", [])
    def typec1_test(self, check_time=5):
        """
        insert_typec1
        :param check_time:检测超时时间，单位：秒
        :return:true/false, msg
        """
        try:
            result = self.io_ctrl_1.read_input(self.ioconfig_1.getint('input', 'Holder1_cover'))
            if result[0] == 0:
                self.io_ctrl_1.write_output(self.ioconfig_1.getint('output', 'typec_1'), ON)
            else:
                return False, "Fail to Holder1_cover"
            start_time = time.time()
            while((time.time() - start_time) < check_time):
                result = self.io_ctrl_1.read_input(self.ioconfig_1.getint('input', 'typec_1_test'))
                if (0 == result[0]):
                    return True, "Success to insert typec_1_test"
            return False, "Fail to insert typec_1_test"
        except Exception as ex:
            return False, "Raise exception(%s)" % str(ex)

    @InterfaceBuild("Display_Interface", "typec1_home", u"release typec_1 home", "typec_1_home", [])
    def typec1_home(self, check_time=5):
        """
        insert_typec1
        :param check_time:检测超时时间，单位：秒
        :return:true/false, msg
        """
        try:
            self.io_ctrl_1.write_output(self.ioconfig_1.getint('output', 'typec_1'), OFF)
            start_time = time.time()
            while((time.time() - start_time) < check_time):
                result = self.io_ctrl_1.read_input(self.ioconfig_1.getint('input', 'typec_1_home'))
                if (0 == result[0]):
                    return True, "Success to insert typec1_home"
            return False, "Fail to insert typec1_home"
        except Exception as ex:
            return False, "Raise exception(%s)" % str(ex)

    @InterfaceBuild("Display_Interface", "typec2_test", u"insert typec_2 测试", "typec_2_test", [])
    def typec2_test(self, check_time=5):
        """
        insert_typec2
        :param check_time:检测超时时间，单位：秒
        :return:true/false, msg
        """
        try:
            result = self.io_ctrl_1.read_input(self.ioconfig_1.getint('input', 'Holder2_cover'))
            if result[0] == 0:
                self.io_ctrl_1.write_output(self.ioconfig_1.getint('output', 'typec_2'), ON)
            else:
                return False, "Fail to Holder2_cover"
            start_time = time.time()
            while ((time.time() - start_time) < check_time):
                result = self.io_ctrl_1.read_input(self.ioconfig_1.getint('input', 'typec_2_test'))
                if (0 == result[0]):
                    return True, "Success to insert typec_2_test"
            return False, "Fail to insert typec_2_test"
        except Exception as ex:
            return False, "Raise exception(%s)" % str(ex)

    @InterfaceBuild("Display_Interface", "typec2_home", u"release typec_2 home", "typec_2_home", [])
    def typec2_home(self, check_time=5):
        """
        insert_typec2
        :param check_time:检测超时时间，单位：秒
        :return:true/false, msg
        """
        try:
            self.io_ctrl_1.write_output(self.ioconfig_1.getint('output', 'typec_2'), OFF)
            start_time = time.time()
            while ((time.time() - start_time) < check_time):
                result = self.io_ctrl_1.read_input(self.ioconfig_1.getint('input', 'typec_2_home'))
                if (0 == result[0]):
                    return True, "Success to insert typec_2_home"
            return False, "Fail to insert typec_2_home"
        except Exception as ex:
            return False, "Raise exception(%s)" % str(ex)
    #
    # @InterfaceBuild("Display_Interface", "start_1", u"start_1 测试", "start_1", [])
    # def start_1(self, check_time=5):
    #     """
    #     start_1
    #     :param check_time:检测超时时间，单位：秒
    #     :return:true/false, msg
    #     """
    #     try:
    #         self.io_ctrl_1.write_output(self.ioconfig_1.getint('output', 'start_1'), ON)
    #         start_time = time.time()
    #         while ((time.time() - start_time) < check_time):
    #             result = self.io_ctrl_1.read_input(self.ioconfig_1.getint('input', 'start_1'))
    #             if (0 == result[0]):
    #                 return True, "Success to start_1"
    #         return False, "Fail to start_1"
    #     except Exception as ex:
    #         return False, "Raise exception(%s)" % str(ex)

    # @InterfaceBuild("Display_Interface", "start_2", u" start_2 测试", "start_2", [])
    # def start_2(self, check_time=5):
    #     """
    #     start_2
    #     :param check_time:检测超时时间，单位：秒
    #     :return:true/false, msg
    #     """
    #     try:
    #         self.io_ctrl_1.write_output(self.ioconfig_1.getint('output', 'start_2'), ON)
    #         start_time = time.time()
    #         while ((time.time() - start_time) < check_time):
    #             result = self.io_ctrl_1.read_input(self.ioconfig_1.getint('input', 'start_2'))
    #             if (0 == result[0]):
    #                 return True, "Success to start_2"
    #         return False, "Fail to start_2"
    #     except Exception as ex:
    #         return False, "Raise exception(%s)" % str(ex)

    def getdevices(self):
        return self.io_ctrl_1,

    def getconfigs(self):
        """
        获取参数配置对象集
        :return: (配置文件参数对象, 如Configini对象)，多个配置文件按照列表方式返回,如:config1,config2,...
        """
        return self.hmdconfig_1, self.ioconfig_1

    def _loop_flow(self):
        """
        老化测试
        :return:
        """
        status, msg = self.typec1_home()
        if status is False or self._loop is False:
            time.sleep(1)
            return
        time.sleep(1)

        status, msg = self.typec2_home()
        if status is False or self._loop is False:
            time.sleep(1)
            return
        time.sleep(1)

        status, msg = self.typec1_test()
        if status is False or self._loop is False:
            time.sleep(1)
            return
        time.sleep(1)

        status, msg = self.typec2_test()
        if status is False or self._loop is False:
            time.sleep(1)
            return
        time.sleep(1)

    def typec_reset(self, index):
        if(index==1):
            self.typec1_home()[0]
        else:
            self.typec2_home()[0]


    def cleanup_control(self, index):
        msg = 'cleanup control success'
        ret = self.typec_reset(index)
        if not ret:
            msg = 'cleanup control fail'
            return ret, msg
        return ret, msg

    def typec_test(self, index):
        if index == 1:
            ret = self.typec1_test()[0]
            return ret
        elif index == 2:
            ret = self.typec2_test()[0]
            return ret

    def init_control(self, index):
        msg = 'Init control success'
        ret = self.check_holder_status(index)
        if not ret:
            msg = '[ERROR] DUT not in Holder{} cover'.format(index)
            return ret, msg
        ret = self.check_position_status(index)
        if not ret:
            msg = '[ERROR] Drawer{} not in position.'.format(index)
            return ret, msg
        ret = self.typec_test(index)
        if not ret:
            msg = '[ERROR] Typec{} insert issue'.format(index)
            return ret, msg
        return ret, msg

    def check_position_status(self, index):
        if index == 1:
            input_name = 'Holder1_test'
        elif index == 2:
            input_name = 'Holder2_test'
        #
        result = self.io_ctrl_1.read_input(self.ioconfig_1.getint('input', input_name))
        print('{} ==============> {}'.format(input_name, result))
        if (0 == result[0]):
            return True
        else:
            return False

    def check_holder_status(self, index):
        if index == 1:
            input_name ='Holder1_cover'
        elif index == 2:
            input_name ='Holder2_cover'
        #
        result = self.io_ctrl_1.read_input(self.ioconfig_1.getint('input', input_name))
        print('{} ==============> {}'.format(input_name, result))
        if (0 == result[0]):
            return True
        else:
            return False

if __name__ == "__main__":
    AppConfigHelper.DEFAULT_CONFIG_DEBUG = True
    sfr = Display_Interface()
    # print (sfr.reset())
    # print (sfr.move_dark1_to_test())
