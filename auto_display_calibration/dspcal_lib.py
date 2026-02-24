import os
import sys
import shutil

# from ColorCalFramework.adb_class import *
from ColorCalFramework.color_basic_class_func import *
#from mars.context import station
# =====================================================
# Mars station safe import (for local debug)
# =====================================================
try:
    from mars.context import station
except ImportError:
    print("⚠ mars module not found, running in LOCAL DEBUG mode")

    class DummyIdentity:
        station_id = "LOCAL_001"
        station_name = "LOCAL_DEBUG"
        project_id = "DEV_PROJECT"

    class DummyConfig:
        station_mode = "DEBUG"

    class DummyStation:
        identity = DummyIdentity()
        config = DummyConfig()

    station = DummyStation()
# from scipy.optimize import curve_fit
# import warnings
# from scipy.optimize import OptimizeWarning
# warnings.simplefilter("error", OptimizeWarning)

# Get Station identity and configs (read-only)
station_id = station.identity.station_id
station_name = station.identity.station_name
project_id = station.identity.project_id
# num_unit = station.num_unit
station_mode = station.config.station_mode
# scan_sn = station.config.scan_sn
# fail_stop = station.config.fail_stop

# Define
DATA_DIR = os.path.join(os.path.expanduser('~'), 'data')

SDR_GAMMA_CAL_FILE_NAME = 'gamma_cal_data.csv'
SDR_GAMUT_CAL_FILE_NAME = 'native_data.csv'
SDR_GAMMA_VAL_FILE_NAME = 'gamma_val_data.csv'
SDR_GAMUT_VAL_FILE_NAME = 'gamut_val_data.csv'

wp_target_tolerance_threshold = 0.004

# -----------------------------------
bl_cal_currents = [0, 10, 25, 50, 75, 85, 90, 95, 97, 98, 100]
bl_val_nits_silver = [0, 20, 50, 100, 150, 200, 250, 300, 350, 400]
bl_val_nits_black = [0, 5, 10, 15, 25, 35, 45, 55, 65, 75]
bl_val_nits_warm_gold = [0, 20, 50, 100, 150, 200, 250, 300, 350, 400]
bl_val_nits_clear = [0, 20, 50, 100, 150, 200, 250, 300, 350, 400]
bl_val_nits = [0, 20, 50, 100, 150, 200, 250, 300, 350, 400]
# -----------------------------------
BL_CAL_FILE_NAME = 'backlight_cal.csv'
BL_CAL_LM_FILE_NAME = 'backlight_cal_linear.csv'
BL_VAL_FILE_NAME = 'backlight_val.csv'
# -----------------------------------
SDR_TARGET_xyY = {
                    'R': (0.6800, 0.3200, 114.487282035),
                    'G': (0.2650, 0.6900, 345.8692609185),
                    'B': (0.1500, 0.0600, 39.64345704685),
                    'W': (0.3127, 0.3290, 500),
                }
HDR_TARGET_xyY = {
                    'R': (0.6800, 0.3200, 114.487282035),
                    'G': (0.2650, 0.6900, 345.8692609185),
                    'B': (0.1500, 0.0600, 39.64345704685),
                    'W': (0.3127, 0.3290, 500),
                }

# CG and pattern combinations to skip validation
color_val_skip = {'Black': ['UI_White', 'UI_Red'],
                  'Silver':['UI_White', 'UI_Red']}

def clean_and_make_dirs(sn):
    if os.path.exists(os.path.join(DATA_DIR, sn)):
        shutil.rmtree(os.path.join(DATA_DIR, sn))
    os.makedirs(os.path.join(DATA_DIR, sn))

def read_mapping_table_by_csv(file_path='./mapping_table.csv', station_id=''):
    mapping_usb_port = {}
    mapping_instrument = {}
    mapping_fixture_number = {}

    with open(file_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if station_id in row['station_id']:
                mapping_usb_port[row['fixture_id']] = row['usb_port']
                mapping_instrument[row['fixture_id']] = row['Hyperion']
                mapping_fixture_number[row['fixture_id']] = int(row['fixture_number'])
                #break

    return mapping_usb_port, mapping_instrument, mapping_fixture_number


def calculate_de00_from_csv(file_path, brightness_mode=BrightnessMode.NORMAL):
    results = {}
    with open(file_path, 'r+') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['Name'] in ['R', 'G', 'B', 'W']:
                results[row['Name']] = [float(row['X']), float(row['Y']), float(row['Z'])]
                if brightness_mode == BrightnessMode.NORMAL:
                    results[row['Name']].append(
                        round(delta_E_calculation(results[row['Name']], SDR_TARGET_xyY[row['Name']], SDR_TARGET_xyY['W']), 2)
                    )
                elif brightness_mode == BrightnessMode.HBM:
                    results[row['Name']].append(
                        round(delta_E_calculation(results[row['Name']], HDR_TARGET_xyY[row['Name']], HDR_TARGET_xyY['W']), 2)
                    )
            else:
                results[row['Name']] = [float(row['X']), float(row['Y']), float(row['Z'])]
    return results


def read_native_rgbw_from_csv(file_path):
    results = {}
    with open(file_path, 'r+') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['R'] == '255' and row['G'] == '255' and row['B'] == '255':
                results['W'] = [round(float(row['X']), 3), round(float(row['Y']), 3), round(float(row['Z']), 3)]
            elif row['R'] == '255' and row['G'] == '0' and row['B'] == '0':
                results['R'] = [round(float(row['X']), 3), round(float(row['Y']), 3), round(float(row['Z']), 3)]
            elif row['R'] == '0' and row['G'] == '255' and row['B'] == '0':
                results['G'] = [round(float(row['X']), 3), round(float(row['Y']), 3), round(float(row['Z']), 3)]
            elif row['R'] == '0' and row['G'] == '0' and row['B'] == '255':
                results['B'] = [round(float(row['X']), 3), round(float(row['Y']), 3), round(float(row['Z']), 3)]
    return results


def read_validation_from_csv(file_path):
    results = {}
    with open(file_path, 'r+') as f:
        reader = csv.DictReader(f)
        for row in reader:
            results[row['Name']] = [round(float(row['X']), 3), round(float(row['Y']), 3), round(float(row['Z']), 3)]
    return results


# convert xy to uv
def xy_to_uv(xy):
    if len(xy) != 2:
      assert False, 'xy_to_uv input variable length must be 2 (xy)'
    x = xy[0]
    y = xy[1]

    u = (4*x)/(-2*x + 12*y +3)
    v = (9*y)/(-2*x + 12*y +3)

    return [u,v]

# convert uv to xy
def uv_to_xy(uv):
    if len(uv) != 2:
      assert False, 'uv_to_xy input variable length must be 2 (uv)'
    u = uv[0]
    v = uv[1]

    x = (9*u)/(6*u - 16*v +12)
    y = (4*v)/(6*u - 16*v +12)

    return [x,y]

# distance from native uv to target uv
def distance_to_target_in_uv(uv, target_uv):
    if len(uv) != 2 or len(target_uv)!= 2:
      assert False, 'uv and target_uv input variable length must be 2 (uv)'

    u = uv[0]
    v = uv[1]
    tu = target_uv[0]
    tv = target_uv[1]

    dist = (u-tu)**2 + (v-tv)**2
    dist = dist**0.5

    return dist

def calculate_new_target_in_uv(uv, target_uv, dist):
    if len(uv) != 2 or len(target_uv)!= 2:
      assert False, 'uv and target_uv input variable length must be 2 (uv)'

    u = uv[0]
    v = uv[1]
    tu = target_uv[0]
    tv = target_uv[1]

    radius_tolerance_circle = wp_target_tolerance_threshold # tolerange value defined by TechEng
    ratio = radius_tolerance_circle / dist

    delta_u = ratio * (u-tu)
    new_target_u = tu+delta_u

    delta_v = ratio * (v-tv)
    new_target_v = tv + delta_v

    return [new_target_u, new_target_v]


def main(argv):

    if len(argv) > 1:
        sn = argv[1].strip()
    else:
        sn = '07131FDEY000J6'

    # mapping_usb_port, mapping_instrument, mapping_fixture_number = read_mapping_table_by_csv(station_id='F7-4F-O6G01FATP-DSP-CAL02')
    # print(mapping_usb_port)
    # print(mapping_instrument)
    # print(mapping_fixture_number)

    # results = read_native_rgbw_from_csv(os.path.join(DATA_DIR, '07131FDEY000J6', SDR_GAMMA_CAL_FILE_NAME))
    # print(results)
    results = calculate_de00_from_csv(os.path.join(DATA_DIR, sn, SDR_GAMUT_VAL_FILE_NAME),
                                      brightness_mode=BrightnessMode.NORMAL)
    print(results)


if __name__ == '__main__':
    main(sys.argv)
