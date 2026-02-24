# 2020-12-19 runhuang@
# 1. add delta_E_validation_with_files

# 2020-11-17 runhuang@
# Added two functions
# 1. def delta_E_calculation_rh
# 2. def read_csv_with_fieldnames(file_path, fieldnames)

# 11/23/2020 claudeliao@
# 1. Add the parts related to HDR

# 11/28/2020 claudeliao@
# 1. Separate SDR and HDR LUTs

"""
Copyright 2020 Google Inc. All Rights Reserved.
Author: claudeliao@
Last updated: 11/28/2020
"""

import numpy as np
import os
import csv
from ColorCalFramework.color_enum import *
import colour
import math
import configparser as cp
import ast
import platform


class MyConfigParser(cp.ConfigParser):
    def __init__(self, defaults=None):
        cp.ConfigParser.__init__(self, defaults=defaults)

    def optionxform(self, option_str):
        return option_str


class Pattern(object):
    def __init__(self, ini_X, ini_Y, ini_Z, ini_R, ini_G, ini_B):
        self.name = ''
        self.X = ini_X
        self.Y = ini_Y
        self.Z = ini_Z
        self.R = ini_R
        self.G = ini_G
        self.B = ini_B
        self.__R_output = 0
        self.__G_output = 0
        self.__B_output = 0
        self.__gamma = 2.2
        self.__alpha = 255
        self.__refresh_rate = 60
        self.__colorspace = ColorSpace.NATIVE
        self.__delay_time = 0.2

    @property
    def X(self):
        return self.__X

    @X.setter
    def X(self, input_X):
        if input_X < 0:
            self.__X = 0
        else:
            self.__X = input_X

    @property
    def Y(self):
        return self.__Y

    @Y.setter
    def Y(self, input_Y):
        if input_Y < 0:
            self.__Y = 0
        else:
            self.__Y = input_Y

    @property
    def Z(self):
        return self.__Z
    @Z.setter
    def Z(self, input_Z):
        if input_Z < 0:
            self.__Z = 0
        else:
            self.__Z = input_Z

    @property
    def XYZ(self):
        return np.array([self.__X, self.__Y, self.__Z])

    @XYZ.setter
    def XYZ(self, input_XYZ):
        input_XYZ[input_XYZ < 0.0] = 0
        self.__X = input_XYZ[0]
        self.__Y = input_XYZ[1]
        self.__Z = input_XYZ[2]

    @property
    def R(self):
        return self.__R

    @R.setter
    def R(self, input_R):
        if input_R < 0:
            self.__R = 0
        elif input_R > 255:
            self.__R = 255
        else:
            self.__R = input_R

    @property
    def G(self):
        return self.__G

    @G.setter
    def G(self, input_G):
        if input_G < 0:
            self.__G = 0
        elif input_G > 255:
            self.__G = 255
        else:
            self.__G = input_G

    @property
    def B(self):
        return self.__B

    @B.setter
    def B(self, input_B):
        if input_B < 0:
            self.__B = 0
        elif input_B > 255:
            self.__B = 255
        else:
            self.__B = input_B

    @property
    def RGB(self):
        return np.array([self.__R, self.__G, self.__B])

    @RGB.setter
    def RGB(self, input_RGB):
        input_RGB[input_RGB < 0] = 0
        self.__R = input_RGB[0]
        self.__G = input_RGB[1]
        self.__B = input_RGB[2]

    @property
    def R_output(self):
        return self.__R_output

    @R_output.setter
    def R_output(self, input_R_output):
        if input_R_output < 0:
            self.__R_output = 0
        elif input_R_output > 1024:
            self.__R_output = 1024
        else:
            self.__R_output = input_R_output

    @property
    def G_output(self):
        return self.__G_output

    @G_output.setter
    def G_output(self, input_G_output):
        if input_G_output < 0:
            self.__G_output = 0
        elif input_G_output > 1024:
            self.__G_output = 1024
        else:
            self.__G_output = input_G_output

    @property
    def B_output(self):
        return self.__B_output

    @B_output.setter
    def B_output(self, input_B_output):
        if input_B_output < 0:
            self.__B_output = 0
        elif input_B_output > 1024:
            self.__B_output = 1024
        else:
            self.__B_output = input_B_output

    @property
    def RGB_output(self):
        return np.array([self.__R_output, self.__G_output, self.__B_output])

    @RGB_output.setter
    def RGB_output(self, input_RGB_output):
        input_RGB_output[input_RGB_output < 0] = 0
        self.__R_output = input_RGB_output[0]
        self.__G_output = input_RGB_output[1]
        self.__B_output = input_RGB_output[2]

    @property
    def gamma(self):
        return self.__gamma

    @gamma.setter
    def gamma(self, input_gamma):
        if input_gamma < 0:
            self.__gamma = 0
        else:
            self.__gamma = input_gamma

    @property
    def delay_time(self):
        return self.__delay_time

    @delay_time.setter
    def delay_time(self, input_delay_time):
        if input_delay_time < 0:
            self.__delay_time = 0
        else:
            self.__delay_time = input_delay_time

    @property
    def colorspace(self):
        return self.__colorspace

    @colorspace.setter
    def colorspace(self, input_colorspace):
        if isinstance(input_colorspace, ColorSpace):
            self.__colorspace = input_colorspace
        else:
            self.__colorspace = ColorSpace.NATIVE


class SDRPatternInfo(object):

    # 20211222 +++ modified by alix
    def __init__(self, lens_color='UNKNOWN'):
        self.__opr = 100

        if lens_color.upper() in ['SILVER', 'BLACK', 'WARM_GOLD', 'CLEAR']:
            mode = lens_color
        else:
            mode = 'SDR'

        self.gamma_cal_patterns = self.read_csv_file('./patterns/{}/gamma_cal_patterns.csv'.format(mode))
        self.gamma_val_patterns = self.read_csv_file('./patterns/{}/gamma_val_patterns.csv'.format(mode))
        self.gamut_cal_patterns = self.read_csv_file('./patterns/{}/gamut_cal_patterns.csv'.format(mode))
        self.gamut_val_patterns = self.read_csv_file('./patterns/{}/gamut_val_patterns.csv'.format(mode))

    @property
    def opr(self):
        return self.__opr

    @opr.setter
    def opr(self, input_opr):
        if input_opr < 0:
            self.__opr = 0
        elif input_opr > 100:
            self.__opr = 100
        else:
            self.__opr = input_opr

    def set_gamma_cal_pattern_by_csv(self, file_path):
        self.gamma_cal_patterns = self.read_csv_file(file_path)

    def set_gamma_val_pattern_by_csv(self, file_path):
        self.gamma_val_patterns = self.read_csv_file(file_path)

    def set_gamut_cal_pattern_by_csv(self, file_path):
        self.gamut_cal_patterns = self.read_csv_file(file_path)

    def set_gamut_val_pattern_by_csv(self, file_path):
        self.gamut_val_patterns = self.read_csv_file(file_path)

    @staticmethod
    def read_csv_file(csv_file_path):
        color_sequence = []
        if os.path.isfile(csv_file_path):
            with open(csv_file_path, 'r+') as f:
                reader = csv.reader(f)
                for row in reader:
                    if 'Name' in row:
                        continue
                    pattern = Pattern(0, 0, 0, int(row[1]), int(row[2]), int(row[3]))
                    pattern.name = row[0]
                    # set color space after row[3]
                    if len(row) == 5:
                        if row[4] == 'NATIVE':
                            pattern.colorspace = ColorSpace.NATIVE
                        elif row[4] == 'P3':
                            pattern.colorspace = ColorSpace.P3
                        elif row[4] == 'SRGB':
                            pattern.colorspace = ColorSpace.SRGB
                        elif row[4] == 'BT2020':
                            pattern.colorspace = ColorSpace.BT2020

                    color_sequence.append(pattern)
            return color_sequence
        else:
            return None


class HDRPatternInfo(object):
    def __init__(self):
        self.__opr = 100
        self.gamma_cal_patterns = self.read_csv_file('./patterns/HDR/gamma_cal_patterns.csv')
        self.gamma_val_patterns = self.read_csv_file('./patterns/HDR/gamma_val_patterns.csv')
        self.gamut_cal_patterns = self.read_csv_file('./patterns/HDR/gamut_cal_patterns.csv')
        self.gamut_val_patterns = self.read_csv_file('./patterns/HDR/gamut_val_patterns.csv')

    @property
    def opr(self):
        return self.__opr

    @opr.setter
    def opr(self, input_opr):
        if input_opr < 0:
            self.__opr = 0
        elif input_opr > 100:
            self.__opr = 100
        else:
            self.__opr = input_opr

    def set_gamma_cal_pattern_by_csv(self, file_path):
        self.gamma_cal_patterns = self.read_csv_file(file_path)

    def set_gamma_val_pattern_by_csv(self, file_path):
        self.gamma_val_patterns = self.read_csv_file(file_path)

    def set_gamut_cal_pattern_by_csv(self, file_path):
        self.gamut_cal_patterns = self.read_csv_file(file_path)

    def set_gamut_val_pattern_by_csv(self, file_path):
        self.gamut_val_patterns = self.read_csv_file(file_path)

    @staticmethod
    def read_csv_file(csv_file_path):
        color_sequence = []
        if os.path.isfile(csv_file_path):
            with open(csv_file_path, 'r+') as f:
                reader = csv.reader(f)
                for row in reader:
                    if 'Name' in row:
                        continue
                    pattern = Pattern(0, 0, 0, int(row[1]), int(row[2]), int(row[3]))
                    pattern.name = row[0]
                    if len(row) == 5:
                        if row[4] == 'NATIVE':
                            pattern.colorspace = ColorSpace.NATIVE
                        elif row[4] == 'P3':
                            pattern.colorspace = ColorSpace.P3
                        elif row[4] == 'SRGB':
                            pattern.colorspace = ColorSpace.SRGB
                        elif row[4] == 'BT2020':
                            pattern.colorspace = ColorSpace.BT2020

                    color_sequence.append(pattern)
            return color_sequence
        else:
            return None


class CalibrationConfig(object):
    def __init__(self,):
        self.__sn = None
        self.__panel_sn = None
        self.__meas_flag = True
        self.__instrument_type = InstrumentType.Hyperion
        self.__pattern_apk = PatternApk.OCTOPUS
        self.__user_matrix = 'factory'
        self.__serial_port = None
        self.__data_dir = './data'
        self.__sh_files_dir = './sh_files'

    @property
    def sn(self):
        return self.__sn

    @sn.setter
    def sn(self, val):
        if isinstance(val, str) or val is None:
            self.__sn = val
        else:
            raise TypeError

    @property
    def panel_sn(self):
        return self.__panel_sn

    @panel_sn.setter
    def panel_sn(self, val):
        if isinstance(val, str) or val is None:
            self.__panel_sn = val
        else:
            raise TypeError

    @property
    def meas_flag(self):
        return self.__meas_flag

    @meas_flag.setter
    def meas_flag(self, val):
        if isinstance(val, bool):
            self.__meas_flag = val
        else:
            raise TypeError

    @property
    def instrument_type(self):
        return self.__instrument_type

    @instrument_type.setter
    def instrument_type(self, input_instrument_type):
        if isinstance(input_instrument_type, InstrumentType):
            self.__instrument_type = input_instrument_type
        else:
            raise TypeError

    @property
    def pattern_apk(self):
        return self.__pattern_apk

    @pattern_apk.setter
    def pattern_apk(self, input_pattern_apk):
        if isinstance(input_pattern_apk, PatternApk):
            self.__pattern_apk = input_pattern_apk
        else:
            raise TypeError

    @property
    def user_matrix(self):
        return self.__user_matrix

    @user_matrix.setter
    def user_matrix(self, input_user_matrix):
        if isinstance(input_user_matrix, str):
            self.__user_matrix = input_user_matrix
        else:
            raise TypeError

    @property
    def serial_port(self):
        return self.__serial_port

    @serial_port.setter
    def serial_port(self, input_serial_port):
        if isinstance(input_serial_port, str) or input_serial_port is None:
            self.__serial_port = input_serial_port
        else:
            raise TypeError

    @property
    def data_dir(self):
        return self.__data_dir

    @data_dir.setter
    def data_dir(self, input_data_dir):
        if isinstance(input_data_dir, str):
            self.__data_dir = input_data_dir
        else:
            raise TypeError

    @property
    def sh_files_dir(self):
        return self.__sh_files_dir

    @sh_files_dir.setter
    def sh_files_dir(self, input_sh_files_dir):
        if isinstance(input_sh_files_dir, str):
            self.__sh_files_dir = input_sh_files_dir
        else:
            raise TypeError

    @property
    def sdr_pre_gamma_cal_adb_file_path(self):
        return os.path.join(self.__sh_files_dir, 'sdr_pre_gamma_cal_adb.sh')

    @property
    def sdr_pre_gamut_cal_adb_file_path(self):
        return os.path.join(self.__sh_files_dir, 'sdr_pre_gamut_cal_adb.sh')

    @property
    def sdr_post_cal_adb_file_path(self):
        return os.path.join(self.__sh_files_dir, 'sdr_post_cal_adb.sh')

    @property
    def sdr_pre_val_adb_file_path(self):
        return os.path.join(self.__sh_files_dir, 'sdr_pre_val_adb.sh')

    @property
    def sdr_post_val_adb_file_path(self):
        return os.path.join(self.__sh_files_dir, 'sdr_post_val_adb.sh')

    @property
    def hdr_pre_gamma_cal_adb_file_path(self):
        return os.path.join(self.__sh_files_dir, 'hdr_pre_gamma_cal_adb.sh')

    @property
    def hdr_pre_gamut_cal_adb_file_path(self):
        return os.path.join(self.__sh_files_dir, 'hdr_pre_gamut_cal_adb.sh')

    @property
    def hdr_post_cal_adb_file_path(self):
        return os.path.join(self.__sh_files_dir, 'hdr_post_cal_adb.sh')

    @property
    def hdr_pre_val_adb_file_path(self):
        return os.path.join(self.__sh_files_dir, 'hdr_pre_val_adb.sh')

    @property
    def hdr_post_val_adb_file_path(self):
        return os.path.join(self.__sh_files_dir, 'hdr_post_val_adb.sh')

    def set_cal_config_by_ini(self, ini_file_path='./ini/cal_config.ini'):
        config = MyConfigParser()
        filename = config.read(ini_file_path)
        if len(filename) != 0:
            for section in config.sections():
                params = config.options(section)
                for param in params:
                    value = ast.literal_eval(config.get(section, param))
                    if param == 'instrument_type':
                        if value == InstrumentType.Hyperion.value:
                            setattr(self, param, InstrumentType.Hyperion)
                        elif value == InstrumentType.CS2000.value:
                            setattr(self, param, InstrumentType.CS2000)
                        elif value == InstrumentType.PRSeries.value:
                            setattr(self, param, InstrumentType.PRSeries)
                        else:
                            setattr(self, param, InstrumentType.Hyperion)
                    elif param == 'pattern_apk':
                        if value == PatternApk.OCTOPUS:
                            setattr(self, param, PatternApk.OCTOPUS)
                        elif value == PatternApk.FIH:
                            setattr(self, param, PatternApk.FIH)
                        else:
                            setattr(self, param, PatternApk.OCTOPUS)
                    else:
                        if value == '' or value == 'None':
                            setattr(self, param, None)
                        else:
                            setattr(self, param, value)
        else:
            return False


class SDRConfig(object):

    def __init__(self, lens_color='UNKNOWN'):

        self.__name = 'SDR'
        self.__gamma_flag = True
        self.__gamut_flag = True
        self.__target_gamma = 2.2
        self.__target_wp_x = 0.3097
        self.__target_wp_y = 0.326
        self.__target_wp_Y = 'Default'
        self.__nodes = 17
        self.__target_gamut = np.array([0.68, 0.32, 0.265, 0.69, 0.15, 0.06])
        self.__bpc = 12

        # 20211222 +++ added by alix re-load patterns
        self.__sdr_pattern_info = SDRPatternInfo(lens_color=lens_color)

        self.__smooth_transition = False
        self.__calculate_gamma_delta_E = False
        self.__calculate_gamut_delta_E = False
        self.__measure_target_flag = False


    @property
    def name(self):
        return self.__name

    @name.setter
    def name(self, val):
        self.__name = val

    @property
    def gamma_flag(self):
        return self.__gamma_flag

    @gamma_flag.setter
    def gamma_flag(self, val):
        if isinstance(val, bool):
            self.__gamma_flag = val
        else:
            raise TypeError

    @property
    def gamut_flag(self):
        return self.__gamut_flag

    @gamut_flag.setter
    def gamut_flag(self, val):
        if isinstance(val, bool):
            self.__gamut_flag = val
        else:
            raise TypeError

    @property
    def target_gamma(self):
        return self.__target_gamma

    @target_gamma.setter
    def target_gamma(self, val):
        if val < 0:
            self.__target_gamma = 0
        else:
            self.__target_gamma = val

    @property
    def target_wp_x(self):
        return self.__target_wp_x

    @target_wp_x.setter
    def target_wp_x(self, val):
        if val < 0:
            self.__target_wp_x = 0
        else:
            self.__target_wp_x = val

    @property
    def target_wp_y(self):
        return self.__target_wp_y

    @target_wp_y.setter
    def target_wp_y(self, val):
        if val < 0:
            self.__target_wp_y = 0
        else:
            self.__target_wp_y = val

    @property
    def target_wp_Y(self):
        return self.__target_wp_Y

    @target_wp_Y.setter
    def target_wp_Y(self, val):
        if isinstance(val, str) and val == 'Default':
            self.__target_wp_Y = val
        elif isinstance(val, float) or isinstance(val, int) and val > 0:
            self.__target_wp_Y = val
        else:
            self.__target_wp_Y = 'Default'

    @property
    def nodes(self):
        return self.__nodes

    @nodes.setter
    def nodes(self, val):
        if isinstance(val, int) and val > 0:
            if val % 2 == 0:
                self.__nodes = val + 1
            else:
                self.__nodes = val
        else:
            raise TypeError

    @property
    def target_gamut(self):
        return self.__target_gamut

    @target_gamut.setter
    def target_gamut(self, val):
        if isinstance(val, list):
            self.__target_gamut = np.array(val)
        elif isinstance(val, np.ndarray):
            self.__target_gamut = val
        else:
            raise TypeError

    @property
    def bpc(self):
        return self.__bpc

    @bpc.setter
    def bpc(self, val):
        if val < 10:
            self.__bpc = 10
        else:
            self.__bpc = val

    @property
    def smooth_transition(self):
        return self.__smooth_transition

    @smooth_transition.setter
    def smooth_transition(self, val):
        if isinstance(val, bool):
            self.__smooth_transition = val
        else:
            raise TypeError

    @property
    def calculate_gamma_delta_E(self):
        return self.__calculate_gamma_delta_E

    @calculate_gamma_delta_E.setter
    def calculate_gamma_delta_E(self, val):
        if isinstance(val, bool):
            self.__calculate_gamma_delta_E = val
        else:
            raise TypeError

    @property
    def calculate_gamut_delta_E(self):
        return self.__calculate_gamut_delta_E

    @calculate_gamut_delta_E.setter
    def calculate_gamut_delta_E(self, val):
        if isinstance(val, bool):
            self.__calculate_gamut_delta_E = val
        else:
            raise TypeError

    @property
    def sdr_pattern_info(self):
        return self.__sdr_pattern_info

    @sdr_pattern_info.setter
    def sdr_pattern_info(self, val):
        self.__sdr_pattern_info = val

    def set_sdr_config_by_ini(self, ini_file_path='./ini/sdr_config.ini'):

        config = MyConfigParser()
        filename = config.read(ini_file_path)
        if len(filename) != 0:
            for section in config.sections():
                params = config.options(section)
                setattr(self, 'name', section)
                for param in params:
                    value = ast.literal_eval(config.get(section, param))
                    setattr(self, param, value)

            return True
        else:
            return False

    @property
    def measure_target_flag(self):
        return self.__measure_target_flag

    @measure_target_flag.setter
    def measure_target_flag(self, val):
        if isinstance(val, bool):
            self.__measure_target_flag = val
        else:
            raise TypeError


class HDRConfig(object):

    def __init__(self):
        self.__name = 'HDR'
        self.__gamma_flag = True
        self.__gamut_flag = False
        self.__target_wp_x = 0.3127
        self.__target_wp_y = 0.329
        self.__target_wp_Y = 'Default'
        self.__nodes = 17
        self.__target_gamut = np.array([0.64, 0.33, 0.3, 0.6, 0.15, 0.06])
        self.__bpc = 12
        self.__hdr_pattern_info = HDRPatternInfo()
        self.__smooth_transition = True
        self.__calculate_gamma_delta_E = False
        self.__calculate_gamut_delta_E = False

    @property
    def name(self):
        return self.__name

    @name.setter
    def name(self, val):
        self.__name = val

    @property
    def gamma_flag(self):
        return self.__gamma_flag

    @gamma_flag.setter
    def gamma_flag(self, val):
        if isinstance(val, bool):
            self.__gamma_flag = val
        else:
            raise TypeError

    @property
    def gamut_flag(self):
        return self.__gamut_flag

    @gamut_flag.setter
    def gamut_flag(self, val):
        if isinstance(val, bool):
            self.__gamut_flag = val
        else:
            raise TypeError

    @property
    def target_wp_x(self):
        return self.__target_wp_x

    @target_wp_x.setter
    def target_wp_x(self, val):
        if val < 0:
            self.__target_wp_x = 0
        else:
            self.__target_wp_x = val

    @property
    def target_wp_y(self):
        return self.__target_wp_y

    @target_wp_y.setter
    def target_wp_y(self, val):
        if val < 0:
            self.__target_wp_y = 0
        else:
            self.__target_wp_y = val

    @property
    def target_wp_Y(self):
        return self.__target_wp_Y

    @target_wp_Y.setter
    def target_wp_Y(self, val):
        if isinstance(val, str) and val == 'Default':
            self.__target_wp_Y = val
        elif isinstance(val, float) or isinstance(val, int) and val > 0:
            self.__target_wp_Y = val
        else:
            self.__target_wp_Y = 'Default'

    @property
    def nodes(self):
        return self.__nodes

    @nodes.setter
    def nodes(self, val):
        if isinstance(val, int) and val > 0:
            if val % 2 == 0:
                self.__nodes = val + 1
            else:
                self.__nodes = val
        else:
            raise TypeError

    @property
    def target_gamut(self):
        return self.__target_gamut

    @target_gamut.setter
    def target_gamut(self, val):
        if isinstance(val, list):
            self.__target_gamut = np.array(val)
        elif isinstance(val, np.ndarray):
            self.__target_gamut = val
        else:
            raise TypeError

    @property
    def bpc(self):
        return self.__bpc

    @bpc.setter
    def bpc(self, val):
        if val < 10:
            self.__bpc = 10
        else:
            self.__bpc = val

    @property
    def smooth_transition(self):
        return self.__smooth_transition

    @smooth_transition.setter
    def smooth_transition(self, val):
        if isinstance(val, bool):
            self.__smooth_transition = val
        else:
            raise TypeError

    @property
    def calculate_gamma_delta_E(self):
        return self.__calculate_gamma_delta_E

    @calculate_gamma_delta_E.setter
    def calculate_gamma_delta_E(self, val):
        if isinstance(val, bool):
            self.__calculate_gamma_delta_E = val
        else:
            raise TypeError

    @property
    def calculate_gamut_delta_E(self):
        return self.__calculate_gamut_delta_E

    @calculate_gamut_delta_E.setter
    def calculate_gamut_delta_E(self, val):
        if isinstance(val, bool):
            self.__calculate_gamut_delta_E = val
        else:
            raise TypeError

    @property
    def hdr_pattern_info(self):
        return self.__hdr_pattern_info

    @hdr_pattern_info.setter
    def hdr_pattern_info(self, val):
        self.__hdr_pattern_info = val

    def set_hdr_config_by_ini(self, ini_file_path='./ini/hdr_config.ini'):
        config = MyConfigParser()
        filename = config.read(ini_file_path)
        if len(filename) != 0:
            for section in config.sections():
                params = config.options(section)
                setattr(self, 'name', section)
                for param in params:
                    value = ast.literal_eval(config.get(section, param))
                    setattr(self, param, value)
            return True
        else:
            return False


class CalibrationData(object):
    def __init__(self):
        self.sdr_linear_gamma_cmd = ''
        self.sdr_linear_gamut_cmd = ''
        self.hdr_linear_gamma_cmd = ''
        self.hdr_linear_gamut_cmd = ''

        self.sdr_gamma_cmd = ''
        self.sdr_gamut_cmd = ''
        self.hdr_gamma_cmd = ''
        self.hdr_gamut_cmd = ''

        self.sdr_precal_rgbw_XYZ = []
        self.sdr_postcal_rgbw_XYZ = []
        self.hdr_precal_rgbw_XYZ = []
        self.hdr_postcal_rgbw_XYZ = []

    def genrate_regammma_cmd_by_csv_linear(self, file_path, brightness_mode=BrightnessMode.NORMAL):
        if brightness_mode == BrightnessMode.NORMAL:
            cmd = 'adb shell displaycolor_service 602 0 0'
        else:
            cmd = 'adb shell displaycolor_service 602 1 0'

        color_sequence = read_csv(file_path)
        for value in color_sequence:
            cmd = cmd + ' ' + str(value)
        return cmd

    def genrate_regammma_cmd_by_csv(self, file_path, brightness_mode=BrightnessMode.NORMAL):
        if brightness_mode == BrightnessMode.NORMAL:
            cmd = 'adb shell displaycolor_service 602 0 1'
        else:
            cmd = 'adb shell displaycolor_service 602 1 1'

        color_sequence = read_csv(file_path)
        for value in color_sequence:
            cmd = cmd + ' ' + str(value)
        return cmd

    def generate_3dlut_sh_by_csv_linear(self, csv_file_path, sh_file_path, brightness_mode=BrightnessMode.NORMAL):
        if brightness_mode == BrightnessMode.NORMAL:
            cmd = 'displaycolor_service 552 0 10 0'
        else:
            cmd = 'displaycolor_service 552 1 10 0'

        color_sequence = read_csv(csv_file_path)
        for value in color_sequence:
            cmd = cmd + ' ' + str(value)

        if os.path.isfile(sh_file_path):
            os.remove(sh_file_path)
        with open(sh_file_path, 'w') as f:
            f.write(cmd)

    def generate_3dlut_sh_by_csv(self, csv_file_path, sh_file_path, brightness_mode=BrightnessMode.NORMAL):
        if brightness_mode == BrightnessMode.NORMAL:
            cmd = 'displaycolor_service 552 0 10 1'
        else:
            cmd = 'displaycolor_service 552 1 10 1'

        color_sequence = read_csv(csv_file_path)
        for value in color_sequence:
            cmd = cmd + ' ' + str(value)

        if os.path.isfile(sh_file_path):
            os.remove(sh_file_path)
        with open(sh_file_path, 'w') as f:
            f.write(cmd)


def delta_E_calculation(mes_XYZ, target_xyY, ref_white_xyY, method='CIE 2000'):
    if len(mes_XYZ) == 3 and len(target_xyY) == 3 and len(ref_white_xyY) == 3:
        mes_xyY = colour.XYZ_to_xyY(mes_XYZ)
        nor_mes_xyY = np.copy(np.asarray(mes_xyY))
        nor_target_xyY = np.copy(np.asarray(target_xyY))
        nor_ref_xyY = np.copy(np.asarray(ref_white_xyY))

        nor_mes_xyY[2] = nor_mes_xyY[2] / nor_ref_xyY[2]
        nor_target_xyY[2] = nor_target_xyY[2] / nor_ref_xyY[2]
        nor_ref_xyY[2] = nor_ref_xyY[2] / nor_ref_xyY[2]
        nor_mes_XYZ = colour.xyY_to_XYZ(np.array(nor_mes_xyY))
        nor_target_XYZ = colour.xyY_to_XYZ(np.array(nor_target_xyY))
        illuminant_xy = (nor_ref_xyY[0], nor_ref_xyY[1])
        mes_Lab = colour.XYZ_to_Lab(nor_mes_XYZ, illuminant_xy)
        target_Lab = colour.XYZ_to_Lab(nor_target_XYZ, illuminant_xy)
        return colour.delta_E(mes_Lab, target_Lab, method)
    else:
        return None


# From Long's script
def srgb_gamma(u):
    b = u <= 0.0031308
    a = 323.0 * u / 25
    c = (np.power(u, 5.0 / 12.0) * 211 - 11) / 200

    return a * b + (1 - b) * c


def srgb_degamma(u):
    b = u <= 0.04045
    a = 25.0 * u / 323
    c = np.power((200 * u + 11) / 211., 12.0 / 5.0)

    return a * b + (1 - b) * c


def gamma_2_2(u):
    return np.power(u, 1 / 2.2)


def degamma_2_2(u):
    return np.power(u, 2.2)


def calculate_target_XYZ(iput_RGBs, reference_white=(0.95, 1.0, 1.1175), gamma=GammaCurve.GAMMA22, colorspace=ColorSpace.P3):
    """
    input:
        iput_RGBs: N*3 array, 8-bits, max value is 255.
    output:
        target_XYZs: N*3 array, normalize with Y1.0
    """
    if colorspace == colorspace.P3:
        Rxy = [0.68, 0.32]
        Gxy = [0.265, 0.69]
        Bxy = [0.15, 0.06]
    elif colorspace == colorspace.SRGB:
        Rxy = [0.64, 0.33]
        Gxy = [0.3, 0.6]
        Bxy = [0.15, 0.06]
    else:
        Rxy = [0.68, 0.32]
        Gxy = [0.265, 0.69]
        Bxy = [0.15, 0.06]

    Xr = Rxy[0] / Rxy[1]
    Yr = 1
    Zr = (1 - Rxy[0] -Rxy[1]) / Rxy[1]

    Xg = Gxy[0] / Gxy[1]
    Yg = 1
    Zg = (1 - Gxy[0] -Gxy[1]) / Gxy[1]

    Xb = Bxy[0] / Bxy[1]
    Yb = 1
    Zb = (1 - Bxy[0] - Bxy[1]) / Bxy[1]

    rf_wp_t = np.array([reference_white]).T

    matrix = np.array([[Xr, Xg, Xb], [Yr, Yg, Yb], [Zr, Zg, Zb]])
    SrSgSb = np.matmul(np.linalg.inv(matrix), rf_wp_t)

    Sr = SrSgSb[0, 0]
    Sg = SrSgSb[1, 0]
    Sb = SrSgSb[2, 0]

    RGB2XYZ = np.array([[Xr*Sr, Xg*Sg, Xb*Sb], [Yr*Sr, Yg*Sg, Yb*Sb], [Zr*Sr, Zg*Sg, Zb*Sb]])

    iput_RGBs = np.array(iput_RGBs)/255
    iput_RGBs[iput_RGBs > 1] = 1

    if gamma == GammaCurve.GAMMA22:
        linear_RGBs = degamma_2_2(iput_RGBs)
    elif gamma == GammaCurve.SRGB_CURVE:
        linear_RGBs = srgb_degamma(iput_RGBs)
    else:
        linear_RGBs = degamma_2_2(iput_RGBs)

    target_XYZs = []
    for rgb in linear_RGBs:
        target_XYZ = np.transpose(np.matmul(RGB2XYZ, np.array([rgb]).T))[0]
        target_XYZs.append(target_XYZ)

    target_XYZs = np.array(target_XYZs)

    return target_XYZs


def delta_E_calculation_rh(mes_XYZs, target_XYZs, illuminant, method = 'CIE 2000'):
    """
    @runhuang
    input:
        mes_XYZs: N*3 array, normalized XYZ with Y=1 @W255
        target_XYZs: N*3 array normalized XYZ with Y=1 @W255
        illuminant: white point,eg.illuminant = (0.3097,0.326)
    output:
        delta_E: N*1 array

    """
    mes_Labs = colour.XYZ_to_Lab(mes_XYZs,illuminant = illuminant)
    target_Labs = colour.XYZ_to_Lab(target_XYZs,illuminant = illuminant)
    delta_E = colour.difference.delta_E(mes_Labs,target_Labs,method)
    return  delta_E


def read_csv_with_fieldnames(file_path, fieldnames):
    """
    read data from csv file with row specified by fieldnames
    input csv file must have a header
    @runhuang

    input:
        csv file with first line as header,
        fieldnames: a list to define the keys of the row to read, the length of the fieldnames is M
    output:
        final_Vals: N*M array,
    """
    # count number of data
    with open (file_path,'r') as csvfile:
        csv_dict_reader = csv.DictReader(csvfile)
        row_count = sum(1 for row in csv_dict_reader)
    # find number of fieldnames
    num_fields = len(fieldnames)

    with open (file_path,'r') as csvfile:
        csv_dict_reader = csv.DictReader(csvfile)
        i = 0
        final_Vals = np.empty(shape = (row_count,num_fields))
        final_Vals[:] = np.NaN
        if (set(fieldnames).issubset(set(csv_dict_reader.fieldnames))):
            for row in csv_dict_reader:
                temp_output= []
                for j in range(0,num_fields):
                    fieldname = fieldnames[j]
                    temp_output.append(float(row[fieldname]))
                final_Vals[i] = np.array(temp_output)
                i = i+1
        else:
            print(fieldnames)
            print('fieldnames do not match the names in csv file')

    return final_Vals


def delta_E_validation_with_files (val_file_path,target_val_file_path,save_file_path,illuminate):
    # need to have input last line to be white255 XYZ
    mes_XYZs = read_csv_with_fieldnames(val_file_path,['X','Y','Z'])
    mes_XYZs = mes_XYZs/mes_XYZs[-1,1]
    target_XYZs = read_csv_with_fieldnames(target_val_file_path,['X','Y','Z'])
    # illuminate = (0.3097,0.326)
    delta_E = delta_E_calculation_rh(mes_XYZs, target_XYZs, illuminate, method='CIE 2000')
    np.savetxt(save_file_path, delta_E, delimiter=",")
    return delta_E


def XYZ_to_uv(measured_XYZ):
    if len(measured_XYZ) == 3:
        measured_xyY = colour.XYZ_to_xy(measured_XYZ)
        measured_uv = colour.xy_to_Luv_uv(measured_xyY)
        return measured_uv
    else:
        return None


def JNCD_calculation(meas_XYZ, target_xyY):
    meas_uv = XYZ_to_uv(meas_XYZ)
    print(meas_uv)
    target_uv = colour.xy_to_Luv_uv(target_xyY[:-1])
    print(target_uv)
    delta_uv = ((meas_uv[0] - target_uv[0])**2 + (meas_uv[1] - target_uv[1])**2)**(1/2)
    print(delta_uv)
    JNCD = delta_uv / 0.004
    return JNCD


def calculate_gamma(current_lum, black_lum, max_lum, current_gray_level, max_gray_level):
    return math.log((current_lum - black_lum) / (max_lum - black_lum)) / math.log(current_gray_level / max_gray_level)


def polynomial_regression(dc, luminance, order):
    result = np.polyfit(dc, luminance, order)
    return result


def read_csv(file_path):
    red = []
    green = []
    blue = []
    if os.path.isfile(file_path):
        with open(file_path, 'r+') as f:
            reader = csv.reader(f)
            for row in reader:
                if 'G' in row:
                    continue
                red.append(int(row[0]))
                green.append(int(row[1]))
                blue.append(int(row[2]))
        color_sequence = red + green + blue
        return color_sequence
    else:
        return None


def write_csv(file_path, columns, results):
    if os.path.isfile(file_path):
        os.remove(file_path)
    if platform.system() == 'Windows':
        with open(file_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(columns)
            for data in results:
                writer.writerow(data)
    else:
        with open(file_path, 'w') as f:
            writer = csv.writer(f)
            writer.writerow(columns)
            for data in results:
                writer.writerow(data)


def main():
    # dc = np.array([0, 8, 12, 16, 24, 32, 48, 64, 96, 128, 160, 192, 224, 255])
    # luminance = np.array([0, 0.295213, 0.631502, 1.151493, 3.171111, 5.811908, 14.30246, 26.606291, 68.761859, 125.378089, 209.86508, 314.577051, 445.628476, 595.372076])
    # print(dc)
    #
    # a = polynomial_regression(dc, luminance, 2)
    # print(a)
    # x = 255
    # y = 0.01050722*(x**2) - 0.37996714*x + 4.66063043
    # print(y)

    cal_config = CalibrationConfig()
    cal_config.set_cal_config_by_ini('./ini/cal_config.ini')

    sdr_config = SDRConfig()
    sdr_config.set_sdr_config_by_ini('./ini/sdr_config.ini')

    hdr_config = HDRConfig()
    hdr_config.set_hdr_config_by_ini('./ini/hdr_config.ini')

    calculate_target_XYZ([[0, 0, 256], [256, 256, 255]])
    input_RGBs = read_csv_with_fieldnames('./gamut_val_data_sdr.csv', ['R', 'G', 'B'])
    measured_XYZs = read_csv_with_fieldnames('./gamut_val_data_sdr.csv', ['X', 'Y', 'Z'])
    max = measured_XYZs[:, 1].max()
    measured_XYZs = measured_XYZs / max
    target_XYZs = calculate_target_XYZ(input_RGBs)
    values = delta_E_calculation_rh(measured_XYZs, target_XYZs, (0.3097, 0.326))
    print(values)
    print(len(values))


if __name__ == '__main__':
    main()
