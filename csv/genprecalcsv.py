import numpy as np
import pandas as pd

# =========================================================
# 1. Color anchor (CIE1931 xy center) – same anchor as post
# =========================================================

COLOR_XY_CENTER = {
    "R":  (0.64,   0.33),
    "G":  (0.30,   0.60),
    "B":  (0.15,   0.06),
    "W":  (0.3127, 0.3290),   # D65
    "NR": (0.575,  0.377),    # Warm Gold / Near-Red
    "NB": (0.2484, 0.3087),   # Near-Blue
}

# =========================================================
# 2. PRE-CAL xy jitter (larger deviation, but still reasonable)
# =========================================================

XY_JITTER_PRE = {
    "R":  (0.030, 0.030),
    "G":  (0.030, 0.030),
    "B":  (0.025, 0.025),
    "W":  (0.020, 0.020),
    "NR": (0.030, 0.030),
    "NB": (0.030, 0.030),
}

# =========================================================
# 3. PRE-CAL Y base + variation (larger spread)
# =========================================================

Y_BASE = {
    "R":  120.0,
    "G":  150.0,
    "B":   80.0,
    "W":  200.0,
    "NR": 110.0,
    "NB":  90.0,
}

Y_VARIATION_PRE = 0.15   # ±15% (uncalibrated)

# =========================================================
# 4. xyY generator (PRE-CAL)
# =========================================================

def generate_xyY_pre(color):
    cx, cy = COLOR_XY_CENTER[color]
    dx, dy = XY_JITTER_PRE[color]

    x = np.random.uniform(cx - dx, cx + dx)
    y = np.random.uniform(cy - dy, cy + dy)

    Y0 = Y_BASE[color]
    Y = Y0 * np.random.uniform(1 - Y_VARIATION_PRE, 1 + Y_VARIATION_PRE)

    return x, y, Y

# =========================================================
# 5. Build PRE-CAL CSV
# =========================================================

def generate_pre_cal_csv(
    output_csv="Bismuth_rgbwk_per_lens.csv",
    units=(0, 1, 2, 3),
    colors=("R", "G", "B", "W", "NR", "NB")
):
    rows = []

    for unit in units:
        for color in colors:
            x, y, Y = generate_xyY_pre(color)

            rows.append({
                "ID": "gold",
                "sequence": "pre",
                "unit_num": unit,
                "color": color,
                "x": round(x, 6),
                "y": round(y, 6),
                "Y": round(Y, 2),
            })

    df = pd.DataFrame(rows)

    # reorder columns
    COLUMN_ORDER = ["ID", "sequence", "unit_num", "color", "x", "y", "Y"]
    df = df[COLUMN_ORDER]

    df.to_csv(output_csv, index=False, encoding="utf-8-sig")

    print(f"✔ PRE-CAL CSV generated: {output_csv}")
    print(df.head())

    return df

# =========================================================
# 6. Run
# =========================================================

if __name__ == "__main__":
    generate_pre_cal_csv(
        output_csv="Bismuth_rgbwk_per_lens.csv",
        units=(0, 1, 2, 3)
    )
