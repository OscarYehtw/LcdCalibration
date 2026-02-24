import argparse
import csv
import numpy as np
import pandas as pd
import os
import platform
import subprocess
import logging
from numpy.linalg import inv
from datetime import datetime
import seaborn as sns
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
from colour.plotting import plot_chromaticity_diagram_CIE1976UCS
from colour.plotting import plot_chromaticity_diagram_CIE1931
from cli.cli import detect_com_ports, enable_lcd, _uart
import Utils.B1_primary_cal_3x3 as primary_cal
from ColorCalFramework.measurement import *
from FixtureControl.DisplayInterface import DisplayInterface
import dspcal_lib as lib
from b1_fct_tools.FCT import *
import logging

# =========================
# SKU-specific defaults
# =========================

DEFAULT_MASTER_P = {
    'r': [0.6442, 0.3338],
    'g': [0.3500, 0.6078],
    'b': [0.1617, 0.0604],
}

DEFAULT_MASTER_W = [0.32, 0.33]

DEFAULT_MEASUREMENTS = {
    'r': np.array([80.406, 39.879, 2.246]),
    'g': np.array([74.952, 143.28, 9.98]),
    'b': np.array([36.464, 14.111, 175.027]),
    'w': np.array([191.351, 196.93, 187.188])
}

dottlined_labels = ['target', 'spec', 'ref']

station = lib.station
station_mode = station.config.station_mode

class TestData:
    def __init__(self, logger=None):
        self.state = {}              # dictionary for port, fixture_number, Hyperion
        self.measurements = {}
        self.phase_results = []
        self.async_dut_index = '0-0' # default to first fixture
        self.logger = logger or logging.getLogger("LCD_CAL") # optional, used in some places

    def AddPhaseResult(self, phase_name, outcome, detail=None):
        self.phase_results.append({
            "phase": phase_name,
            "outcome": outcome,
            "detail": detail
        })

    def GetPhaseResult(self):
        return self.phase_results

def setup_logger():
    logger = logging.getLogger("LCD_CAL")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        ch = logging.StreamHandler()
        fmt = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(message)s"
        )
        ch.setFormatter(fmt)
        logger.addHandler(ch)

    return logger

def read_master_csv(path):
    """
    master.csv columns:
    Color, x, y
    """
    master_p = {}
    master_w = None

    color_map = {
        'red': 'r',
        'green': 'g',
        'blue': 'b',
        'white': 'w'
    }

    with open(path, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            color = row['Color'].strip().lower()
            if color not in color_map:
                continue

            key = color_map[color]
            x = float(row['x'])
            y = float(row['y'])

            if key in ['r', 'g', 'b']:
                master_p[key] = [x, y]
            else:
                master_w = [x, y]

    if len(master_p) != 3 or master_w is None:
        raise ValueError("master.csv must contain RGB + White (xy)")

    return master_p, master_w

def read_measured_csv(path, sequence="pre"):
    """
    measured.csv columns:
    Color, X, Y, Z
    """
    measurements = {}

    with open(path, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['sequence'].strip().lower() != sequence:
                continue

            color = row['color'].strip().lower()
            if color not in {'r', 'g', 'b', 'w'}:
                continue

            X = float(row['X'])
            Y = float(row['Y'])
            Z = float(row['Z'])

            measurements[color] = np.array([X, Y, Z])

    if set(measurements.keys()) != {'r', 'g', 'b', 'w'}:
        raise ValueError("measured.csv must contain RGB + White (XYZ)")

    return measurements

def LM_gen_per_len(self, df_r, df_g, df_b, df_w, unit_number):
    rd = df_r[df_r['unit_num']==unit_number]
    gd = df_g[df_g['unit_num']==unit_number]
    bd = df_b[df_b['unit_num']==unit_number]
    wd = df_w[df_w['unit_num']==unit_number]

    # Device RGB
    rxyY1 = [rd['x'].tolist()[0], rd['y'].tolist()[0], rd['Y'].tolist()[0]]
    gxyY1 = [gd['x'].tolist()[0], gd['y'].tolist()[0], gd['Y'].tolist()[0]]
    bxyY1 = [bd['x'].tolist()[0], bd['y'].tolist()[0], bd['Y'].tolist()[0]]
    wxyY1 = [wd['x'].tolist()[0], wd['y'].tolist()[0], wd['Y'].tolist()[0]]

    ## Target white : take the mean from the distribution
    w_x_target = df_w.describe().loc[['mean']]['x'][0].astype(float)
    w_y_target = df_w.describe().loc[['mean']]['y'][0].astype(float)

    ## Target RGB for warm gold : take minimum from the distribution

    r_x_target = df_r.describe().loc[['min']]['x'][0].astype(float)
    r_y_target = df_r.describe().loc[['mean']]['y'][0].astype(float)

    g_x_target = df_g.describe().loc[['mean']]['x'][0].astype(float)
    g_y_target = df_g.describe().loc[['min']]['y'][0].astype(float)

    b_x_target = df_b.describe().loc[['max']]['x'][0].astype(float)
    b_y_target = df_b.describe().loc[['mean']]['y'][0].astype(float)

    # Target RGB for warm gold
    xyzr = [r_x_target, r_y_target, 1 - r_x_target - r_y_target ]
    xyzg = [g_x_target, g_y_target, 1 - g_x_target - g_y_target ]
    xyzb = [b_x_target, b_y_target, 1 - b_x_target - b_y_target ]
    xyzw = [w_x_target, w_y_target, 1 - w_x_target - w_y_target ]

    dict_target_rgb = {'r':xyzr,
                       'g':xyzg,
                       'b':xyzb,
                       'w':xyzw
                        }

    dict_device_rgb = {'r':rxyY1,
                       'g':gxyY1,
                       'b':bxyY1,
                       'w':wxyY1
                       }

    dict_post_cal_val_pattern , M, Md, Mf, max_RGB_dc = primary_cal.LM_3x3(dict_device_rgb , dict_target_rgb)

    return dict_post_cal_val_pattern, M, Md, Mf, max_RGB_dc

def XYZ_to_device_RGB(self, Md, target_XYZ, max_RGB_dc):
    # input argument format: target_XYZ = [x, x, x]

    XYZ_in = np.array( [target_XYZ] ).reshape((3,1))
    RGBp = np.matmul(inv(Md), XYZ_in)
    RGBp[RGBp<0]=0

    #max_RGB_dc = 1.0
    RGBp_dc = np.round((RGBp**(1/2.2))/max_RGB_dc*255)
    RGBp_dc[RGBp_dc>255]=255

    temp = RGBp_dc.squeeze().tolist()
    RGBp_hex = [hex(int(x)) for x in temp]

    return RGBp_dc, RGBp_hex

def check_string_in_key(check_strings, key):
    for string in check_strings:
        if string in key:
            return True

    return False

def plot_1931_color_comparison(dict_data, gamut_boundary, title=""):
    plot_chromaticity_diagram_CIE1931(show=False,
                                         title=False,
                                         tight_layout=True)

    for key, data in dict_data.items():

        if 'x' not in data.columns or 'y' not in data.columns:
            continue

        if check_string_in_key(dottlined_labels, key):
            plt.scatter(data['x'], data['y'], label=key, edgecolor='white',
                        marker='s', s=60, facecolors='none')
        else:
            plt.scatter(data['x'], data['y'], label=key, edgecolor='black')

    plt.plot(gamut_boundary[:, 0], gamut_boundary[:, 1], c='black', linestyle='--')
    plt.xlim([0, 1])
    plt.ylim([0, 1])
    plt.title('CIE1931 color, {}'.format(title))
    plt.tight_layout()
    plt.legend(facecolor='#AAAAAAAA')
    #plt.show()

def plot_1931_color_comparison_v2(data, gamut_boundary , hue, title=""):
    plot_chromaticity_diagram_CIE1931(show=False,
                                         title=False,
                                         tight_layout=True)

    sns.scatterplot(x='x', y='y', data=data , hue = hue)

    plt.plot(gamut_boundary[:, 0], gamut_boundary[:, 1], c='black')
    plt.xlim([0, 1])
    plt.ylim([0, 1])
    plt.title('CIE1931 color, {}'.format(title))
    plt.tight_layout()
    plt.legend(facecolor='#AAAAAAAA')
    #plt.show()

def plot_1931_color_comparison_v3(data, gamut_boundary1, gamut_boundary2, hue , title=""):
    plot_chromaticity_diagram_CIE1931(show=False,
                                         title=False,
                                         tight_layout=True)

    sns.scatterplot(x='x', y='y', data=data , hue = hue)

    plt.plot(gamut_boundary1[:, 0], gamut_boundary1[:, 1], c='black')
    plt.plot(gamut_boundary2[:, 0], gamut_boundary2[:, 1], c='black')
    plt.xlim([0, 1])
    plt.ylim([0, 1])
    plt.title('CIE1931 color, {}'.format(title))
    plt.tight_layout()
    plt.legend(facecolor='#AAAAAAAA')
    #plt.show()

def color_analysis_by_group(df, color, title, hue="color"):
    df_color = df[df["ID"]==color]
    df_r = df_color[df_color["color"]=="R"]
    df_g = df_color[df_color["color"]=="G"]
    df_b = df_color[df_color["color"]=="B"]
    df_w = df_color[df_color["color"]=="W"]
    df_nr = df_color[df_color["color"]=="NR"]
    df_nb = df_color[df_color["color"]=="NB"]


    plt.figure(figsize=(15,5))
    plt.subplot(121)
    ax = sns.boxplot(x="color", hue = hue, y="x", data=df_color)
    plt.title('CIE1931 color, {}'.format(title))
    plt.subplot(122)
    ax = sns.boxplot(x="color", hue = hue, y="y", data=df_color)
    plt.title('CIE1931 color, {}'.format(title))

    #plt.show()

    dict_color = {'df_r':df_r,
                  'df_g':df_g,
                  'df_b':df_b,
                  'df_w':df_w,
                  'df_nr':df_nr,
                  'df_nb':df_nb
                }

    return df_color, dict_color

def xyY_to_XYZ(x, y, Y=1.0):
    """Converts CIE chromaticity (x, y) and Luminance Y to Tristimulus XYZ."""
    if y == 0: return np.array([0.0, 0.0, 0.0])
    X = (x * Y) / y
    Z = ((1 - x - y) * Y) / y
    return np.array([X, Y, Z])

def XYZ_to_xy(XYZ):
    """Converts Tristimulus XYZ to chromaticity coordinates (x, y)."""
    total = np.sum(XYZ)
    if total == 0: return [0.0, 0.0]
    return [XYZ[0] / total, XYZ[1] / total]

def xy_to_uv(x, y):
    """Converts CIE xy to UCS uv (CIE 1960)."""
    denom = -2*x + 12*y + 3
    if denom == 0: return np.array([0.0, 0.0])
    return np.array([4*x / denom, 9*y / denom])

def uv_to_xy(u, v):
    """Converts UCS uv to CIE xy."""
    denom = 6*u - 16*v + 12
    if denom == 0: return np.array([0.0, 0.0])
    return np.array([9*u / denom, 4*v / denom])

def run_if_cal_is_pass(test_data):
    print(f"station_mode: {station_mode}")
    if station_mode != 'RELIABILITY':
      phase_results = test_data.GetPhaseResult()
      if phase_results[1]['outcome'] == 'PASS' or phase_results[1]['outcome'] == 'SCOF_PASS':
        return True
      else:
        return False
    else:
      return True


class DisplayCalibrator:
    """
    Standard 3x3 Display Calibration Procedure with White Point Adaptation.
    """
    def __init__(self, max_delta_uv=0.004):
        self.max_delta_uv = max_delta_uv
 
        self.master_path = "master.csv"
        self.measured_path = "measured.csv"
        self.cs160_path = "cs-160.csv"
        self.auto_color_list = ["W", "R", "G", "B"]
        self.color_rgb_map = {
            "W": (255, 255, 255),
            "R": (255, 0, 0),
            "G": (0, 255, 0),
            "B": (0, 0, 255),
        }

        # Fixed setting
        self.brightness = 100

    def calculate_adapted_white(self, master_w_xy, native_w_xy):
        """
        Calculates a compromise target white point.
        Moves the target white toward the device's native white by a maximum UV distance.
        """
        m_uv = xy_to_uv(*master_w_xy)
        n_uv = xy_to_uv(*native_w_xy)
        vec = n_uv - m_uv
        dist = np.linalg.norm(vec)
        
        if dist <= self.max_delta_uv:
            final_uv = n_uv
        else:
            unit_vec = vec / dist
            final_uv = m_uv + (unit_vec * self.max_delta_uv)
        return uv_to_xy(*final_uv)

    def compute_matrix(self, measurements, master_primaries, master_white):
        """
        Computes the final 3x3 calibration matrix (Mf).
        
        Args:
            measurements: dict of XYZ arrays for {'r', 'g', 'b', 'w'}
            master_primaries: dict of xy lists for {'r', 'g', 'b'}
            master_white: list of [x, y] for the ideal target white
        """
        # 1. Determine Target White Point (Adapted to Device)
        native_w_xy = XYZ_to_xy(measurements['w'])
        target_w_xy = self.calculate_adapted_white(master_white, native_w_xy)
        
        # 2. Solve for Target Matrix (Ms)
        # We find the intensities of the Master Primaries that sum to the 
        # Target White Point at the device's native luminance.
        Y_native = measurements['w'][1]
        W_target_xyz = xyY_to_XYZ(*target_w_xy, Y=Y_native)
        
        Pr_xyz = xyY_to_XYZ(*master_primaries['r'], Y=1.0)
        Pg_xyz = xyY_to_XYZ(*master_primaries['g'], Y=1.0)
        Pb_xyz = xyY_to_XYZ(*master_primaries['b'], Y=1.0)
        P_matrix = np.column_stack((Pr_xyz, Pg_xyz, Pb_xyz))
        
        # S_vector represents the required linear RGB intensities (scaling)
        S_vector = np.matmul(inv(P_matrix), W_target_xyz)
        Ms = P_matrix * S_vector 

        # 3. Construct Device Matrix (Md) from native measurements
        Md = np.column_stack((measurements['r'], measurements['g'], measurements['b']))

        # 4. Calculate Calibration Matrix (Mf)
        # Md * Mf = Ms  => Mf = inv(Md) * Ms
        Mf = np.matmul(inv(Md), Ms)
        
        # 5. Normalization (Scale to max drive of 1.0)
        white_drive = np.matmul(Mf, np.array([1, 1, 1]))
        max_drive = np.max(white_drive)
        
        return {
            'Mf': Mf,
            'Md': Md,
            'Ms': Ms,
            'RGB_max': max_drive ** (1/2.2), #Gamma correction
            'target_white': target_w_xy
        }

    def save_calibration_data(self, test_data):
        master_p = DEFAULT_MASTER_P
        master_w = DEFAULT_MASTER_W
        measurements = DEFAULT_MEASUREMENTS
               
        master_p, master_w = read_master_csv(self.master_path)
        #measurements = read_measured_csv(self.measured_path)
        result = self.compute_matrix(measurements, master_p, master_w)

        # Assign usb port & Hyperion to current fixture
        #test_data.async_dut_index = '1-0'
        test_data.state['port'] = mapping_usb_port[test_data.async_dut_index]
        test_data.state['Hyperion'] = mapping_hyperion[test_data.async_dut_index]
        test_data.state['fixture_number'] = mapping_fixture_number[test_data.async_dut_index]

        disp_cal_md = result['Md']
        disp_cal_ms = result['Ms']
        disp_cal_mf = result['Mf']
        rgb_max = result['RGB_max']

        cmd_format = '{:.5f},{:.5f},{:.5f},{:.5f},{:.5f},{:.5f},{:.5f},{:.5f},{:.5f}'
        mat = disp_cal_md
        disp_cal_md_str = cmd_format.format(mat[0, 0], mat[0, 1], mat[0, 2],
                                            mat[1, 0], mat[1, 1], mat[1, 2],
                                            mat[2, 0], mat[2, 1], mat[2, 2])
        mat = disp_cal_ms
        disp_cal_ms_str = cmd_format.format(mat[0, 0], mat[0, 1], mat[0, 2],
                                            mat[1, 0], mat[1, 1], mat[1, 2],
                                            mat[2, 0], mat[2, 1], mat[2, 2])
        mat = disp_cal_mf
        disp_cal_mf_str = cmd_format.format(mat[0, 0], mat[0, 1], mat[0, 2],
                                            mat[1, 0], mat[1, 1], mat[1, 2],
                                            mat[2, 0], mat[2, 1], mat[2, 2])
        rgb_max_str = '{:.5f}'.format(rgb_max)
               
        # write matrices to sysenv
        flag = 1
        # ----- disp_cal_md
        if b1_fct[test_data.state['fixture_number']].set_sysenv_retries(test_data, 'disp_cal_md', disp_cal_md_str):
          print('write the disp_cal_md succeed!')
          test_data.logger.info('write the disp_cal_md succeed!')
        else:
          flag = 0
          print('[ERROR] write the disp_cal_md failed!')
          test_data.logger.error('[ERROR] write the disp_cal_md failed!')
        # ----- disp_cal_ms
        if b1_fct[test_data.state['fixture_number']].set_sysenv_retries(test_data, 'disp_cal_ms', disp_cal_ms_str):
          print('write the disp_cal_ms succeed!')
          test_data.logger.info('write the disp_cal_ms succeed!')
        else:
          flag = 0
          print('[ERROR] write the disp_cal_ms failed!')
          test_data.logger.error('[ERROR] write the disp_cal_ms failed!')
        # ----- disp_cal_mf
        if b1_fct[test_data.state['fixture_number']].set_sysenv_retries(test_data, 'disp_cal_mf', disp_cal_mf_str):
          print('write the disp_cal_mf succeed!')
          test_data.logger.info('write the disp_cal_mf succeed!')
        else:
          flag = 0
          print('[ERROR] write the disp_cal_mf failed!')
          test_data.logger.error('[ERROR] write the disp_cal_mf failed!')
        # ----- disp_cal_rgb_max
        if b1_fct[test_data.state['fixture_number']].set_sysenv_retries(test_data, 'disp_cal_rgb_max', rgb_max_str):
          print('write the disp_cal_rgb_max succeed!')
          test_data.logger.info('write the disp_cal_rgb_max succeed!')
        else:
          flag = 0
          print('[ERROR] write the disp_cal_rgb_max failed!')
          test_data.logger.error('[ERROR] write the disp_cal_rgb_max failed!')
        #
        test_data.state['disp_cal_md'] = disp_cal_md
        test_data.state['disp_cal_ms'] = disp_cal_ms
        test_data.state['disp_cal_mf'] = disp_cal_mf
        test_data.state['disp_cal_rgb_max'] = rgb_max
        test_data.measurements['disp_cal_md'] = disp_cal_md_str
        test_data.measurements['disp_cal_ms'] = disp_cal_ms_str
        test_data.measurements['disp_cal_mf'] = disp_cal_mf_str
        test_data.measurements['disp_cal_rgb_max'] = rgb_max_str
        test_data.measurements['calibration_data'] = flag

        # for cal file check
        test_data.state['disp_cal_md_str'] = disp_cal_md_str
        test_data.state['disp_cal_ms_str'] = disp_cal_ms_str
        test_data.state['disp_cal_mf_str'] = disp_cal_mf_str
        test_data.state['disp_cal_rgb_max_str'] = rgb_max_str

    def run_apply_wrbg(self, mode="pre", panel_id="gold"):
        file_exists = os.path.exists(self.measured_path)
        with open(self.measured_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow([
                    "TimeStamp", "ID", "sequence", "color",
                    "R", "G", "B",
                    "x", "y",
                    "u`", "v`",
                    "X", "Y", "Z"
                ])

            if mode == "post":
               master_p = DEFAULT_MASTER_P
               master_w = DEFAULT_MASTER_W
               measurements = DEFAULT_MEASUREMENTS
               
               master_p, master_w = read_master_csv(self.master_path)
               #measurements = read_measured_csv(self.measured_path)
               result = self.compute_matrix(measurements, master_p, master_w)
               if 0:
                  # Output
                  print("master_p, master_w:\n", master_p, master_w)
                  print("measurements:\n", measurements)
                  print("Calibration Matrix (Mf):\n", result['Mf'])
                  print("Target Matrix (Ms):\n", result['Ms'])
                  print("Device Matrix (Md):\n", result['Md'])
                  print("RGB_max:", result['RGB_max'])
                  print("Adapted Target White:", result['target_white'])

            for color in self.auto_color_list:
                #r, g, b = self.color_rgb_map[color]

                # choose PRE / POST RGB
                if mode == "pre":
                    r, g, b = self.color_rgb_map[color]
                else:
                    gamma = 2.2
                    inv_gamma = 1.0 / gamma
                    rgb_orig = np.array(self.color_rgb_map[color], dtype=float)

                    # Native RGB: Normalized Gamma Correction
                    rgb_linear = np.power(rgb_orig / 255.0, gamma)

                    # Adjusted RGB
                    rgb_transformed = np.dot(result['Mf'], rgb_linear)

                    # UX Color: UX Color: Vectorized processing for Clipping and Gamma restoration
                    rgb_corrected = np.power(np.maximum(0.0, rgb_transformed), inv_gamma) * (255.0 / result['RGB_max'])

                    # Rounding and type conversion (Alternative to round, min, and int)
                    r, g, b = np.clip(np.round(rgb_corrected), 0, 255).astype(int)

                    if 0:
                       print(f"       Color: {color}")
                       print(f"  Native RGB: {rgb_orig}")
                       print(f"Adjusted RGB: [{r} {g} {b}]")

                if 0:
                   print(f"Apply {color}: RGB={r,g,b}, BL={self.brightness}")

                # UART
                system = platform.system()
                if system == "Windows":
                    _uart.port = "COM3"
                elif system == "Linux":
                    _uart.port = "/dev/ttyACM0"
                else:
                    print(f"[WARNING] Unsupported platform: {system}")
                    continue

                if not enable_lcd(r, g, b, self.brightness):
                    print("[FAIL] LCD control failed")
                    #continue

                # Launch measurement tool
                exe_path = os.path.join("CS160OneShot", "OneShotMeasurementTool.exe")
                try:
                    subprocess.run(exe_path, check=True, shell=True)
                except Exception as e:
                    print(f"Failed to launch {exe_path}: {e}")

                # 讀 cs160.csv 寫入 measured.csv
                if not os.path.exists(self.cs160_path):
                    print(f"[WARN] {self.cs160_path} not found, skipping")
                    continue

                with open(self.cs160_path, newline='', encoding='utf-8-sig') as csf:
                    reader = csv.DictReader(csf)
                    for row in reader:
                        try:
                            u = float(row["u`"])
                            v = float(row["v`"])
                            X = float(row["X"])
                            Y = float(row["Y"])
                            Z = float(row["Z"])
                        except (KeyError, ValueError):
                            continue

                        total = X + Y + Z
                        x = X / total if total != 0 else 0
                        y = Y / total if total != 0 else 0

                        timestamp = datetime.now().isoformat(timespec="seconds")

                        writer.writerow([
                            timestamp, panel_id, mode, color, r, g, b,
                            round(x, 6), round(y, 6),
                            round(u, 6), round(v, 6),
                            round(X, 6), round(Y, 6), round(Z, 6)
                        ])
                #rint(f"[INFO] Measurement saved for {color}")

        if 0:
         # Remove measurement file to force next cycle to generate fresh data
         if os.path.exists(self.cs160_path):
             os.remove(self.cs160_path)

        if mode == "pre":
          test_data.AddPhaseResult("PRE", "PASS")
        else:
          test_data.AddPhaseResult("POST", "SCOF_PASS")

        if mode == "post":
          if run_if_cal_is_pass(test_data):
            self.save_calibration_data(test_data)

        #print("[DONE] All colors completed")

if __name__ == "__main__":

    # Declare user defined configs
    # Initialize test_data
    test_data = TestData(setup_logger())

    # only for offline validation
    disabled_fixture_ctrl = False
    disabled_device_ctrl = False

    # Read mapping table by csv
    mapping_usb_port, mapping_hyperion, mapping_fixture_number = lib.read_mapping_table_by_csv(station_id='B1_BN3-BF1_FATP-DISP-CAL_IN23A-03')
    print('****** mapping_usb_port: {}'.format(mapping_usb_port))
    print('****** mapping_hyperion: {}'.format(mapping_hyperion))
    print('****** mapping_fixture_number: {}'.format(mapping_fixture_number))

    # Objects Instantiate
    print('[FixtureControl] fixture control {}.'.format('enabled' if not disabled_fixture_ctrl else 'disabled'))
    #if not disabled_fixture_ctrl:
    #  fixture_ctrl = DisplayInterface('FATP-DISP-CAL')

    b1_fct0 = FCT_CTRL(demo=disabled_device_ctrl)
    b1_fct1 = FCT_CTRL(demo=disabled_device_ctrl)
    b1_fct = [b1_fct0, b1_fct1]

    parser = argparse.ArgumentParser(
        description="Generate 3x3 Color Correction Matrix (CCM)"
    )

    parser.add_argument(
        "--master",
        default=None,
        help="Path to master.csv (target xy). If omitted, use default master_p/master_w."
    )

    parser.add_argument(
        "--measured",
        default=None,
        help="Path to measured.csv (measured XYZ). If omitted, use default measurements."
    )

    parser.add_argument(
        "--id",
        default="gold",
        help="Panel ID (default: gold). e.g. gold = warm gold cover"
    )

    parser.add_argument(
        "--max-delta-uv",
        type=float,
        default=0.004,
        help="Max white point adaptation distance in u'v'"
    )

    args = parser.parse_args()

    # initialise data of lists.
    p3_gamut_xy = np.array(
        [[0.68, 0.32],
         [0.265, 0.69],
         [0.15, 0.06],
         [0.68, 0.32]])

    NTSC_gamut_xy = np.array(
        [[0.67, 0.33],
         [0.21, 0.71],
         [0.14, 0.08],
         [0.67, 0.33]])

    sRGB_gamut_xy = np.array(
        [[0.64, 0.33],
         [0.3, 0.6],
         [0.15, 0.06],
         [0.64, 0.33]])

    data_spec_xy = {'x':[0.64, 0.3, 0.15],
            'y':[0.33, 0.6, 0.06]}

    data_NTSC_xy = {'x':[0.67, 0.21, 0.14],
            'y':[0.33, 0.71, 0.08]}

    # Create DataFrame
    df_spec_xy = pd.DataFrame(data_spec_xy)
    df_spec_xy['ID'] = "target"

    # Load CSVs
    # master_p, master_w = read_master_csv(args.master)
    # measurements = read_measured_csv(args.measured)

    # -------------------------
    # Load master (target)
    # -------------------------
    if args.master:
        print(f"[INFO] Loading master from CSV: {args.master}")
        master_p, master_w = read_master_csv(args.master)
    else:
        print("[INFO] Using default master_p / master_w")
        master_p = DEFAULT_MASTER_P
        master_w = DEFAULT_MASTER_W

    # -------------------------
    # Load measurements
    # -------------------------
    if args.measured:
        print(f"[INFO] Loading measurements from CSV: {args.measured}")
        measurements = read_measured_csv(args.measured)
    else:
        print("[INFO] Using default measurements")
        measurements = DEFAULT_MEASUREMENTS

    # Run calibration
    cal = DisplayCalibrator(max_delta_uv=args.max_delta_uv)

    cal.run_apply_wrbg("pre", panel_id=args.id)
    cal.run_apply_wrbg("post", panel_id=args.id)

    ## Data reading abd example plot
    df_color_factory = pd.read_csv(cal.measured_path, encoding = 'utf-8')

    #print("df_color_factory",df_color_factory)
    #print("df_spec xy",df_spec_xy)

    dict_color_xy = {
        'ref-target-sRGB':df_spec_xy,
        'B1 Primary':df_color_factory
    }

    if 0:
       plot_1931_color_comparison_v2(df_color_factory, gamut_boundary = sRGB_gamut_xy, hue= "ID", title= "precal gamut all lens")
       plot_1931_color_comparison_v3(df_color_factory, gamut_boundary1 = sRGB_gamut_xy, gamut_boundary2 = NTSC_gamut_xy, hue= "ID",  title="precal gamut all lens")

    #########################################################
    ##
    ## Warm gold data analysis and 3x3 matrix generation
    ##
    #########################################################

    # Create DataFrame
    df_spec_xy = pd.DataFrame(data_spec_xy)
    df_spec_xy['ID'] = "sRGB"
    df_NTSC_xy = pd.DataFrame(data_NTSC_xy)
    df_NTSC_xy['ID'] = "NTSC"
    #print(df_color_factory[df_color_factory["ID"]=="g"])

    dict_color_xy = {
        'ref-target-sRGB':df_spec_xy,
        'ref-target-NTSC':df_NTSC_xy,
        'Bismuth Primary':df_color_factory[df_color_factory["ID"]=="gold"]
    }

    if 0:
       plot_1931_color_comparison(dict_color_xy, gamut_boundary = NTSC_gamut_xy, title= "precal_warm_gold")

       ### Color distribution
       df_gold_color, dict_color = color_analysis_by_group(df_color_factory, "gold", title = "PreCal color distribution")

       df_gold_r = dict_color["df_r"]
       df_gold_g = dict_color["df_g"]
       df_gold_b = dict_color["df_b"]
       df_gold_w = dict_color["df_w"]
       df_gold_nr = dict_color["df_nr"]
       df_gold_nb = dict_color["df_nb"]

       df_gold_r.describe().to_csv('./csv/r_describe.csv', encoding='utf-8')
       df_gold_g.describe().to_csv('./csv/g_describe.csv', encoding='utf-8')
       df_gold_b.describe().to_csv('./csv/b_describe.csv', encoding='utf-8')
       df_gold_w.describe().to_csv('./csv/w_describe.csv', encoding='utf-8')

       # This function takes care of matrix generation
       # M, Md, Mf = LM_gen_per_len(df_gold_r, df_gold_g, df_gold_b, df_gold_w, unit_number)

       ## warm gold unit 0
       for i in range(4):

           unit_number = i
           ## check post cal RGBW pattern
           dict_post_cal_val_pattern, M, Md, Mf, max_RGB_dc = LM_gen_per_len(df_gold_r, df_gold_g, df_gold_b, df_gold_w, unit_number)
           print("Unit_number: ", unit_number)
           print(dict_post_cal_val_pattern)

           ## Estimated nest red and blue RGB for given XYZ target
           df_gold_nr_unit = df_gold_nr[df_gold_nr['unit_num']==unit_number]
           #t_xyY = [df_gold_nr_unit['x'].tolist()[0], df_gold_nr_unit['y'].tolist()[0], df_gold_nr_unit['Y'].tolist()[0]]
           t_xyY = [0.575, 0.377, df_gold_nr_unit['Y'].tolist()[0]]
           t_XYZ = [ t_xyY[0]/t_xyY[1] * t_xyY[2] , t_xyY[2], (1 - t_xyY[0]-t_xyY[1])/t_xyY[1] * t_xyY[2] ]
           RGBp_dc, RGBp_hex = XYZ_to_device_RGB(Md, t_XYZ, max_RGB_dc)
           print("Estimated NR RGB basedon target XYZ: ",t_XYZ, RGBp_dc, RGBp_hex)

           df_gold_nb_unit = df_gold_nb[df_gold_nb['unit_num']==unit_number]
           #t_xyY = [df_gold_nb_unit['x'].tolist()[0], df_gold_nb_unit['y'].tolist()[0], df_gold_nb_unit['Y'].tolist()[0]]
           t_xyY = [0.2484, 0.3087, df_gold_nb_unit['Y'].tolist()[0]]
           t_XYZ = [ t_xyY[0]/t_xyY[1] * t_xyY[2] , t_xyY[2], (1 - t_xyY[0]-t_xyY[1])/t_xyY[1] * t_xyY[2] ]
           RGBp_dc, RGBp_hex = XYZ_to_device_RGB(Md, t_XYZ, max_RGB_dc)
           print("Estimated NB RGB basedon target XYZ: ",t_XYZ, RGBp_dc, RGBp_hex)

    if 0:
       ## Post cal data plot
       df_color = pd.read_csv('Bismuth_rgbwk_per_lens_post_cal.csv', encoding = 'big5')
       df_color_post = df_color[df_color["sequence"]=="post"]
       dict_color_xy = {
           'ref-target-sRGB':df_spec_xy,
           'ref-target-NTSC':df_NTSC_xy,
           'Bismuth Primary':df_color_post[df_color_post["ID"]=="gold"]
       }
       plot_1931_color_comparison_v2(df_color_post, gamut_boundary = sRGB_gamut_xy , hue= "ID", title ="post_cal gamut all lens")
       plot_1931_color_comparison_v3(df_color_post, gamut_boundary1 = sRGB_gamut_xy, gamut_boundary2 = NTSC_gamut_xy,  hue= "ID", title="post_cal gamut all lens")
       plot_1931_color_comparison_v3(df_color, gamut_boundary1 = sRGB_gamut_xy, gamut_boundary2 = NTSC_gamut_xy,  hue= "sequence", title="pre and post_cal gamut all lens")
       plot_1931_color_comparison(dict_color_xy, gamut_boundary = NTSC_gamut_xy,  title ="post_cal gamut : warm gold")

    ## Pre-Post-new Color comparison for warm gold
    #df_color_post = pd.read_csv('Bismuth_rgbwk_per_lens_pre_post_cal_comparison.csv', encoding = 'big5')
    df_color_post = pd.read_csv(cal.measured_path, encoding = 'utf-8')
    dict_color_xy = {
        'ref-target-sRGB':df_spec_xy,
        'ref-target-NTSC':df_NTSC_xy,
        'Bismuth Primary':df_color_post[df_color_post["ID"]=="gold"]
    }
    plot_1931_color_comparison_v2(df_color_post, gamut_boundary = sRGB_gamut_xy,  hue= "sequence",)
    plot_1931_color_comparison_v3(df_color_post, gamut_boundary1 = sRGB_gamut_xy, gamut_boundary2 = NTSC_gamut_xy,  hue= "sequence",)
    plot_1931_color_comparison(dict_color_xy, gamut_boundary = NTSC_gamut_xy,  title =" Pre-Post-New Color comparison : warm gold")

    df_color_post_R = df_color_post[df_color_post["color"]=="R"]
    df_color_post_G = df_color_post[df_color_post["color"]=="G"]
    df_color_post_B = df_color_post[df_color_post["color"]=="B"]
    df_color_post_W = df_color_post[df_color_post["color"]=="W"]
    df_color_post_NR = df_color_post[df_color_post["color"]=="NR"]
    df_color_post_NB = df_color_post[df_color_post["color"]=="NB"]

    ### Color distribution
    df_gold_color, dict_color = color_analysis_by_group(df_color_post, "gold", hue = "sequence", title = " Color distribution comparison")
    df_gold_color, dict_color = color_analysis_by_group(df_color_post_R, "gold", hue = "sequence", title = "Color distribution : Red")
    df_gold_color, dict_color = color_analysis_by_group(df_color_post_G, "gold", hue = "sequence", title = "Color distribution : Green")
    df_gold_color, dict_color = color_analysis_by_group(df_color_post_B, "gold", hue = "sequence", title = "Color distribution : Blue")
    df_gold_color, dict_color = color_analysis_by_group(df_color_post_W, "gold", hue = "sequence", title = "Color distribution : White")
    df_gold_color, dict_color = color_analysis_by_group(df_color_post_NR, "gold", hue = "sequence", title = "Color distribution : Nest Red")
    df_gold_color, dict_color = color_analysis_by_group(df_color_post_NB, "gold", hue = "sequence", title = "Color distribution : Nest Blue")

    plt.show()
