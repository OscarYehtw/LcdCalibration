# !/usr/bin/python
# -*- coding: UTF-8 -*-

'''
Created on 2020-10-09

@author: lzq
'''

'''v1.0.0.3      2021/08/09   @liaoying
1.Integration API , add FATP-DISP-TURNTABLE station.
'''

'''v1.0.0.2      2021/04/06   @luzhiqiang
1.Integration API , add FATP-DISP-CAL/FATP-DISP-OA station.
'''

'''v1.0.0.1      2021/03/25   @luzhiqiang
1.Integration API , for Artfact/Artfact-STRED station.
'''

try:
    from FixtureControl.DisplayInterface_Artifact_STRED import DisplayInterface_Artifact_STRED
    from FixtureControl.DisplayInterface_Artifact import DisplayInterface_Artifact
    from FixtureControl.DisplayInterface_Cal import DisplayInterface_Cal
    from FixtureControl.DisplayInterface_P7OA import DisplayInterface_P7OA
    from FixtureControl.DisplayInterface_TurnTable import DisplayInterface_TurnTable
    from FixtureControl.Bismuth_Display_Interface import Bismuth_Display_Interface
except:
    from DisplayInterface_Artifact_STRED import DisplayInterface_Artifact_STRED
    from DisplayInterface_Artifact import DisplayInterface_Artifact
    from DisplayInterface_Cal import DisplayInterface_Cal
    from DisplayInterface_P7OA import DisplayInterface_P7OA
    from DisplayInterface_TurnTable import DisplayInterface_TurnTable
    from Bismuth_Display_Interface import Bismuth_Display_Interface

class DisplayInterface(object):
    def __init__(self, station_name):
        self.station_name = station_name.upper()
        print (self.station_name, '----------------')
        self.Display = None
        self.init()

    def init(self):
        '''
        init DisplayInterface.
        :return:
        '''
        if self.station_name == 'FATP-DISP-ARTIFACT-STERD':
            self.Display = DisplayInterface_Artifact_STRED()
        elif self.station_name == 'FATP-DISP-ARTIFACT':
            self.Display = DisplayInterface_Artifact()
        # elif self.station_name == 'FATP-DISP-CAL':
        #     self.Display = DisplayInterface_Cal()
        elif self.station_name == 'FATP-DISP-OA':
            self.Display = DisplayInterface_P7OA()
        elif self.station_name == 'FATP-DISP-TURNTABLE':
            self.Display = DisplayInterface_TurnTable()
        elif self.station_name == 'FATP-DISP-CAL':
            self.Display = Bismuth_Display_Interface()
    # for Artifact station.
    def Init_Control(self, index=1):
        '''
        For Mars init control.
        :return: True/False, msg
        '''
        ret, msg = self.Display.init_control(index)
        return ret, msg

    def Cleanup_Control(self, index=1):
        '''
        For Mars cleanup control.
        :return: True/False, msg
        '''
        ret, msg = self.Display.cleanup_control(index)
        return ret, msg

    def Light_Open(self):
        '''
        Turn on the Ring light, for Artifact station.
        :return: True/False
        '''
        ret = self.Display.light_open()
        return ret

    def Light_Close(self):
        '''
        Turn off the Ring light, for Artifact station.
        :return: True/False
        '''
        ret = self.Display.light_close()
        return ret

    def SetBrightness(self, channel, value):
        '''
        Turn on/off the Ring light, insert (channel, value). for Artifact station.
        :param channel: Controller channel
        :param value: Controller Current value
        :return: True/False
        '''
        ret = self.Display.setbrightness(channel, value)
        return ret

    def Check_Trigger(self):
        '''
        For Mars Trigger Start test.
        :return: True/False
        '''
        return self.Display.check_start_button_status()

    # for Display cal station
    def check_position_status(self, index=1):
        '''
        Check drawer in position ,for Display cal station
        :param index: slot number
        :return: True/False
        '''
        return self.Display.check_position_status(index)

    def typec_test(self, index=1):
        '''
        Typec test ,for Display cal/OA station
        :param index: slot number
        :return: True/False
        '''
        return self.Display.typec_test(index)

    def typec_reset(self, index=1):
        '''
        Typec reset ,for Display cal station
        :param index: slot number
        :return: True/False
        '''
        return self.Display.typec_reset(index)

    # for Display OA station
    def check_door_status(self):
        '''
        Check door status ,for Display OA/DOE station
        :return: True/False
        '''
        return self.Display.check_door_status()

    def OA_reset(self):
        '''
        OA reset ,for Display OA/DOE station
        :return: True/False
        '''
        return self.Display.OA_reset()

    def spin_move_to_test(self):
        '''
        Spin test ,for Display OA/DOE station
        :return: True/False
        '''
        return self.Display.spin_move_to_test()

    def spin_move_to_home(self):
        '''
        Spin reset ,for Display OA/DOE station
        :return: True/False
        '''
        return self.Display.spin_move_to_home()

    def move_to_center(self):
        '''
        Motor move to center ,for Display OA/DOE station
        :return: True/False
        '''
        return self.Display.move_to_center()

    def move_to_down(self):
        '''
        Motor move to down ,for Display OA/DOE station
        :return: True/False
        '''
        return self.Display.move_to_down()
    
    def get_dut_index(self):
        '''
        get dut index,for Display Turn Table station
        :return: 1/2 fail -1
        '''
        return self.Display.get_dut_inside_index()

if __name__ == '__main__':
    test = DisplayInterface('FATP-DISP-TURNTABLE')
    test.Init_Control()
    import time
    time.sleep(5)
    test.Cleanup_Control()
