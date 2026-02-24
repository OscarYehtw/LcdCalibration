"""
Copyright 2021 Google Inc. All Rights Reserved.
Author: alixweng@
Last updated: 1/12/2022
"""

import sys
import os
import time
import subprocess as sp
import logging
import re

__version__ = '1.0.0'


def get_fct_port(usb_port):
    try:
        cmd = 'ls /sys/bus/usb/devices/{}/tty'.format(usb_port)
        results = sp.check_output(cmd, stderr=sp.STDOUT, shell=True)
        print(results)
        results = results.decode('utf-8')
        if results.find('ttyACM') >= 0:
            num1, num2 = re.search('ttyACM\d', results).span()
            fct_port = results[num1:num2]
            print('get_fct_port() ------> {}'.format(fct_port))
            return '/dev/{}'.format(fct_port)
        else:
            print('[ERROR] Can not find the get_fct_port!!')
            return ''
    except AttributeError:
        print('[ERROR] Can not find the get_fct_port!!')
        return ''

class FCT_CTRL(object):

    def __init__(self, demo=False):

        self.FCT_TIMEOUT = 5
        self.tool_name = 'b1_fct'
        self.usb_index = 0
        self.usb_port = '/dev/ttyACM0'
        self.serial_number = ''
        self.initialized = False
        self.demo_f = demo
        self.lens_color = '-1'

        return

    def init(self, usb_index=0, usb_port='/dev/ttyACM0', tool_name='b1_fct'):

        self.tool_name = tool_name
        self.usb_index = usb_index
        self.usb_port = usb_port

        LOG_FILE_PATH = './log_{}.txt'.format(usb_index)
        print('LOG_FILE_PATH: {}'.format(LOG_FILE_PATH))
        if os.path.exists(LOG_FILE_PATH):
            os.remove(LOG_FILE_PATH)
        time.sleep(0.1)
        logging.basicConfig(filename=LOG_FILE_PATH,
                            filemode='a',
                            format='%(asctime)s,%(msecs)d %(levelname)s %(message)s',
                            datefmt='%H:%M:%S',
                            level=logging.INFO)

        #self.get_devices()
        self.initialized = True

        ret = 'tool name: {}\n'.format(self.tool_name)
        ret += 'usb index: {}\n'.format(self.usb_index)
        ret += 'usb port: {}\n'.format(self.usb_port)
        ret += 'initialized: {}\n'.format(self.initialized)

        print(ret)
        logging.info(ret)
        return ret

    def teardown(self):
        cmd = './b1_fct_tools/{} -p {} shell reset'.format(self.tool_name, self.usb_port)

        if not self.demo_f:
            ret = self.fct(cmd)
        else:
            ret = 'ACK: reset\r\nresult = 0'

        print(ret)
        logging.info(ret)
        return ret

    def fct(self, cmd, delay_time=5):

        if '-p' in cmd:
            cmd = cmd.replace('-p', '-t %s -p' % str(self.FCT_TIMEOUT))
        p = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.PIPE, shell=True)
        pre_time = time.time()

        while True:
            if p.poll() is not None or cmd.find('shell reset') >= 0:
                break
            total_time = time.time() - pre_time
            if delay_time and total_time > delay_time:
                p.terminate()
                msg = '[ERROR] fct timeout!!'
                raise Exception(msg)
                print(msg)
                logging.info(msg)
            time.sleep(.1)

        ret = p.communicate()
        print(ret)
        logging.info(ret)

        try:
            if len(ret) > 0:
                ret = ret[0].decode('utf-8')
        except Exception as ex:
            print('[ERROR] fct command error: {}'.format(ex))

        return ret

    def get_devices(self):
        cmd = './b1_fct_tools/{} devices -l'.format(self.tool_name, self.usb_port)

        if not self.demo_f:
            ret = self.fct(cmd)
        else:
            ret = 'result = 0'

        print(ret)
        logging.info(ret)
        if ret.find('result = 0') >= 0:
            return True
        else:
            return False

    def get_version(self):
        cmd = './b1_fct_tools/{} -p {} shell version'.format(self.tool_name, self.usb_port)

        if not self.demo_f:
            ret = self.fct(cmd)
            if ret.find('result = 0') >= 0:
                s = ret.split('\n')
                for ss in s:
                    if 'version    :' in ss:
                        version = ss.strip().split(':')[1].strip()
                        break
            else:
                version = ret
        else:
            ret = 'ACK: version\r\nresult = 0'
            version = 'DEMO'

        print(ret)
        logging.info(ret)
        return version

    def get_serial_number(self):

        # if self.tool_name.find('z1_fct') >= 0:
        #     # z1_fct
        cmd = './b1_fct_tools/{} -p {} shell sysenv get wip#'.format(self.tool_name, self.usb_port)
        # else:
        #     # b1_fct
        #     cmd = './b1_fct_tools/{} -p {} shell sysenv get serial#'.format(self.tool_name, self.usb_port)

        if not self.demo_f:
            ret = self.fct(cmd)
        else:
            ret = 'ACK: sysenv\r\n12345678\r\nresult = 0'

        print(ret)
        logging.info(ret)

        if ret != '':
            sn = ret.split('\r\n')[1].strip()
        else:
            sn = ''

        self.serial_number = sn
        return self.serial_number

    def get_lens_color(self):
        cmd = './b1_fct_tools/{} -p {} shell sysenv get lens_color'.format(self.tool_name, self.usb_port)

        # 0: Silver, 1: Rose, 2: Nickel, 3: Black, 4: Warm gold
        if not self.demo_f:
            ret = self.fct(cmd)
            if ret.find('result = 0') >= 0:
                s = ret.split('\n')
                self.lens_color = s[1].strip()
            else:
                self.lens_color = -1
        else:
            ret = 'ACK: sysenv\r\nresult = 0'
            self.lens_color = '0'

        print(ret)
        logging.info(ret)
        return self.lens_color


    def get_sysenv(self, param='TEST'):

        cmd = './b1_fct_tools/{} -p {} shell sysenv get {}'.format(self.tool_name, self.usb_port, param)

        if not self.demo_f:
            ret = self.fct(cmd)
        else:
            ret = 'ACK: sysenv\r\nresult = 0'
        print(ret)
        logging.info(ret)

        if ret.find('result = 0') >= 0:
            return True, ret
        else:
            return False, ret

    # params
    # - serial#
    # - LCD_BRIGHTNESS_COEFFICIENT
    # - LCD_BRIGHTNESS_EXP_COEFFICIENT
    # - disp_cal_md
    # - disp_cal_ms
    # - disp_cal_mf
    # - disp_cal_rgb_max
    def set_sysenv(self, param='TEST', value='0'):

        cmd = './b1_fct_tools/{} -p {} shell sysenv set {} {}'.format(self.tool_name, self.usb_port, param, value)

        if not self.demo_f:
            ret = self.fct(cmd)
        else:
            ret = 'ACK: sysenv\r\nresult = 0'
        print(ret)
        logging.info(ret)

        if ret.find('result = 0') >= 0:
            return True
        else:
            return False

    def set_sysenv_retries(self, test_data, param='TEST', value='0'):

        retries = 10
        retries_delay = 0.5

        cmd = './b1_fct_tools/{} -p {} shell sysenv set {} {}'.format(self.tool_name, self.usb_port, param, value)

        if not self.demo_f:
            ret = self.fct(cmd)
        else:
            ret = 'ACK: sysenv\r\nresult = 0'
        print(ret)
        logging.info(ret)

        if ret.find('result = 0') < 0:
            # FCT failed
            # retries
            while retries >= 0:
              time.sleep(retries_delay)
              test_data.logger.info(f'[WARNING] FCT failed. Retries left: {retries}')
              retries = retries - 1
              ret = self.fct(cmd)

              if ret.find('result = 0') >= 0:
                  return True

        if ret.find('result = 0') >= 0:
            return True
        else:
            return False


    def set_current(self, value=50):
        cmd = './b1_fct_tools/{} -p {} shell fct-bl set_current_percent {}'.format(self.tool_name, self.usb_port, value)

        if not self.demo_f:
            ret = self.fct(cmd)
        else:
            ret = 'ACK: fct-bl\r\nresult = 0'
        print(ret)
        logging.info(ret)

        if ret.find('result = 0') >= 0:
            return True
        else:
            return False

    def set_brightness(self, value=255):
        cmd = './b1_fct_tools/{} -p {} shell fct-bl set_brightness_nits {}'.format(self.tool_name, self.usb_port, value)

        if not self.demo_f:
            ret = self.fct(cmd)
        else:
            ret = 'ACK: fct-bl\r\nresult = 0'
        print(ret)
        logging.info(ret)

        # get current
        s = ret.split('Backlight current set to ')[1]
        current = int(s.split('%')[0].strip())
        # print('current ------------> {}'.format(current))
        # -----------

        if ret.find('result = 0') >= 0:
            return True, current
        else:
            return False, current

    def rgb2hex(self, r=255, g=255, b=255):
        rh = hex(r).split('0x')[1].zfill(2)
        gh = hex(g).split('0x')[1].zfill(2)
        bh = hex(b).split('0x')[1].zfill(2)
        return '{}{}{}'.format(rh, gh, bh)

    def hex2rgb(self, rgbh='000000'):

        if rgbh.find('0x') >= 0:
            rgbh = rgbh.replace('0x', '')
        elif rgbh.find('#') >= 0:
            rgbh = rgbh.replace('#', '')

        rh = rgbh[0:2]
        gh = rgbh[2:4]
        bh = rgbh[4:6]
        r = int(rh, 16)
        g = int(gh, 16)
        b = int(bh, 16)
        return r, g, b

    # draw custom patterns
    def set_background_color(self, r=255, g=255, b=255):
        cmd = './b1_fct_tools/{} -p {} shell lcd fill 0x{}'.format(self.tool_name, self.usb_port, self.rgb2hex(r=r, g=g, b=b))

        if not self.demo_f:
            ret = self.fct(cmd)
        else:
            ret = 'ACK: fct-lcd\r\nresult = 0'
        print(ret)
        logging.info(ret)

        if ret.find('result = 0') >= 0:
            return True
        else:
            return False


    # draw custom calibrated patterns
    def set_calib_background_color(self, r=255, g=255, b=255):
        cmd = './b1_fct_tools/{} -p {} shell lcd fill_calib 0x{}'.format(self.tool_name, self.usb_port, self.rgb2hex(r=r, g=g, b=b))

        if not self.demo_f:
            ret = self.fct(cmd)
        else:
            ret = 'ACK: fct-lcd\r\nresult = 0'
        print(ret)
        logging.info(ret)

        if ret.find('result = 0') >= 0:
            return True
        else:
            return False

    # draw specific patterns
    def set_pattern(self, clr='G255'):

        COLOR_CODE = {
            'R': self.rgb2hex(r=255, g=0, b=0),
            'G': self.rgb2hex(r=0, g=255, b=0),
            'B': self.rgb2hex(r=0, g=0, b=255),
            'G0': self.rgb2hex(r=0, g=0, b=0),
            'G32': self.rgb2hex(r=32, g=32, b=32),
            'G48': self.rgb2hex(r=48, g=48, b=48),
            'G127': self.rgb2hex(r=127, g=127, b=127),
            'G192': self.rgb2hex(r=192, g=192, b=192),
            'G255': self.rgb2hex(r=255, g=255, b=255),
            'C': self.rgb2hex(r=0, g=255, b=255),
            'M': self.rgb2hex(r=255, g=0, b=255),
            'Y': self.rgb2hex(r=255, g=255, b=0),
        }
        cmd = './b1_fct_tools/{} -p {} shell lcd fill 0x{}'.format(self.tool_name, self.usb_port, COLOR_CODE[clr])

        if not self.demo_f:
            ret = self.fct(cmd)
        else:
            ret = 'ACK: fct-lcd\r\nresult = 0'
        print(ret)
        logging.info(ret)

        if ret.find('result = 0') >= 0:
            return True
        else:
            return False

    # draw cross pattern for alignment
    def set_crosshair(self, r=255, g=255, b=255):

        cmd = './b1_fct_tools/{} -p {} shell lcd crosshair 0x{}'.format(self.tool_name, self.usb_port,
                                                                        self.rgb2hex(r=r, g=g, b=b))
        if not self.demo_f:
            ret = self.fct(cmd)
        else:
            ret = 'ACK: fct-lcd\r\nresult = 0'
        print(ret)
        logging.info(ret)

        if ret.find('result = 0') >= 0:
            return True
        else:
            return False

    # draw checkerboard pattern
    def set_checker(self, r=255, g=255, b=255, checker_size=50):

        cmd = './b1_fct_tools/{} -p {} shell lcd checker 0x{} {}'.format(self.tool_name, self.usb_port,
                                                                         self.rgb2hex(r=r, g=g, b=b),
                                                                         checker_size)
        if not self.demo_f:
            ret = self.fct(cmd)
        else:
            ret = 'ACK: fct-lcd\r\nresult = 0'
        print(ret)
        logging.info(ret)

        if ret.find('result = 0') >= 0:
            return True
        else:
            return False

    def fct_demo(self):
        ret = 'ACK: demo\r\nresult = 0'
        return ret

    def auto_ship_mode(self):
        cmd = './b1_fct_tools/{} -p {} shell auto-ship-mode force'.format(self.tool_name, self.usb_port)

        if not self.demo_f:
            ret = self.fct(cmd)
        else:
            ret = 'ACK: auto-ship-mode\r\nresult = 0'

        print(ret)
        logging.info(ret)

        if ret.find('result = 0') >= 0:
            return True
        else:
            return False

    # default: 0, linear mapping: 2
    def set_bl_linear_mapping(self, mapping=0):
        cmd = './b1_fct_tools/{} -p {} shell backlight config 0 0 {}'.format(self.tool_name, self.usb_port, mapping)

        if not self.demo_f:
            ret = self.fct(cmd)
        else:
            ret = 'ACK: backlight\r\nresult = 0'

        print(ret)
        logging.info(ret)

        if ret.find('result = 0') >= 0:
            return True
        else:
            return False

    def calc_current_ma(self, test_data):
        cmd = './b1_fct_tools/{} -p {} shell fct-bl calc_current_ma'.format(self.tool_name, self.usb_port)

        logging.info('calc_current_ma')
        logging.info(f'send: {cmd}')
        # test_data.logger.info('calc_current_ma')
        # test_data.logger.info(f'send: {cmd}')

        if not self.demo_f:
            ret = self.fct(cmd)
        else:
            ret = 'ACK: fct-bl\r\nBacklight current = 100.00 mA\r\nresult = 0'

        print(ret)
        logging.info(ret)
        # test_data.logger.info(f'ret: {ret}')

        if ret.find('result = 0') >= 0:
            result = ret.split('\r\n')[1].split('=')[1].split('mA')[0].strip()
            # test_data.logger.info(f'true, {result}')
            return True, result
        else:
            # test_data.logger.info(f'fail, 0')
            return False, 0


    # P2.2 to add battery info
    def get_battery_voltage(self, test_data):
        cmd = './b1_fct_tools/{} -p {} shell fct-bat voltage'.format(self.tool_name, self.usb_port)

        test_data.logger.info('get_battery_voltage')

        if not self.demo_f:
            ret = self.fct(cmd)
        else:
            ret = 'ACK: fct-bat\r\nadc count: 3874\r\nvbat voltage: 3973mV\r\nresult = 0'

        if ret.find('result = 0') >= 0:
            result = ret.split('\r\n')[2].split(':')[1].split('mV')[0].strip()
            return True, result
        else:
            return False, 0

    # P2.2 to add battery info
    def get_battery_temp(self, test_data):
        cmd = './b1_fct_tools/{} -p {} shell fct-bat temp'.format(self.tool_name, self.usb_port)

        test_data.logger.info('get_battery_temp')

        if not self.demo_f:
            ret = self.fct(cmd)
        else:
            ret = 'ACK: fct-bat\r\nADC count: 510 => R thermistor 99415\r\nvbat temperature: 25.19°C\r\nresult = 0'

        if ret.find('result = 0') >= 0:
            result = ret.split('\r\n')[2].split(':')[1].split('°C')[0].strip()
            return True, result
        else:
            return False, 0

    # EVT, enable and disable battery charge
    def set_battery_charge_status(self, test_data, status):
        if status == 1:
            cmd = './b1_fct_tools/{} -p {} shell fct-bat charger enable'.format(self.tool_name, self.usb_port)
        elif status == 0:
            cmd = './b1_fct_tools/{} -p {} shell fct-bat charger disable'.format(self.tool_name, self.usb_port)
        else:
            return False

        test_data.logger.info(f'set_battery_charge_status, {status}')

        if not self.demo_f:
            ret = self.fct(cmd)
        elif status == 1:
            ret = 'ACK: fct-bat\r\nnlpmic_charger_set_enabled: kRegChg2Conf 0x60 = 0xea\r\nresult = 0\r\nDONE 0'
        else:
            ret = 'ACK: fct-bat\r\nnlpmic_charger_set_disabled: kRegChg2Conf 0x60 = 0x6a\r\nresult = 0\r\nDONE 0'

        if ret.find('result = 0') >= 0:
            test_data.logger.info('set_battery_charge_status SUCCESS')
            return True
        else:
            test_data.logger.info('WARNING: set_battery_charge_status FAIL (non-fatal)')
            return False

    def get_battery_charge_status(self, test_data):
        cmd = './b1_fct_tools/{} -p {} shell fct-bat charger status'.format(self.tool_name, self.usb_port)

        test_data.logger.info('get_battery_charge_status')

        if not self.demo_f:
            ret = self.fct(cmd)
        else:
            ret = 'ACK: fct-bat\r\nnlpmic_charger_is_enabled: kRegChg2Conf 0x60 = 0xea\r\nresult = 0\r\nDONE 0'

        if ret.find('result = 0') >= 0:
            result = ret.split('\r\n')[1].split(':')[0]
            test_data.logger.info(f'get_battery_charge_status SUCCESS, {result}')
            return True, result
        else:
            test_data.logger.error('WARNING: get_battery_charge_status FAIL (non-fatal)')
            return False, 0


def main():
    fct = FCT_CTRL()
    fct.init(usb_index=0, usb_port='/dev/ttyACM0', tool_name='b1_fct')
    print('Serial Number: {}'.format(fct.get_serial_number()))
    return


if __name__ == '__main__':
    main()
