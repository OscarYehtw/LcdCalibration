import csv
import numpy as np
from numpy.linalg import inv

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

def read_measured_csv(path):
    """
    measured.csv columns:
    Color, X, Y, Z
    """
    measurements = {}

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
            X = float(row['X'])
            Y = float(row['Y'])
            Z = float(row['Z'])

            measurements[key] = np.array([X, Y, Z])

    if set(measurements.keys()) != {'r', 'g', 'b', 'w'}:
        raise ValueError("measured.csv must contain RGB + White (XYZ)")

    return measurements

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

class DisplayCalibrator:
    """
    Standard 3x3 Display Calibration Procedure with White Point Adaptation.
    """
    def __init__(self, max_delta_uv=0.004):
        self.max_delta_uv = max_delta_uv

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

if __name__ == "__main__":
    # Example Usage
    master_csv = "master.csv"
    measured_csv = "measured.csv"

    # These will be SKU-specific constants.
    master_p = {
        'r': [0.6442, 0.3338],
        'g': [0.3500, 0.6078],
        'b': [0.1617, 0.0604], 
    }
    master_w = [0.32, 0.33]

    # Example device measurements (XYZ)
    measurements = {
        'r': np.array([80.406, 39.879, 2.246]),
        'g': np.array([74.952, 143.28, 9.98]),
        'b': np.array([36.464, 14.111, 175.027]),
        'w': np.array([191.351, 196.93, 187.188])
    }

    master_p, master_w = read_master_csv(master_csv)
    measurements = read_measured_csv(measured_csv)

    cal = DisplayCalibrator(max_delta_uv=0.004)
    result = cal.compute_matrix(measurements, master_p, master_w)

    if 1:
     print("Calibration Matrix (Mf):\n", result['Mf'])
     print("Targe Matrix (Ms):\n", result['Ms'])
     print("Device Matrix (Md):\n", result['Md'])
     print("RGB_max:", result['RGB_max'])
     print("Adapted Target White:", result['target_white'])
