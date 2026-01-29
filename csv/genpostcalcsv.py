import numpy as np
import pandas as pd

# =========================================================
# 1. Color anchor (CIE1931 xy center)
# =========================================================

COLOR_XY_CENTER = {
    "R":  (0.64,   0.33),
    "G":  (0.30,   0.60),
    "B":  (0.15,   0.06),
    "W":  (0.3127, 0.3290),   # D65
    "NR": (0.575,  0.377),    # Near-Red / Warm Gold
    "NB": (0.2484, 0.3087),   # Near-Blue
}

# xy jitter range (do NOT deviate from main color)
XY_JITTER = {
    "R":  (0.010, 0.010),
    "G":  (0.010, 0.010),
    "B":  (0.008, 0.008),
    "W":  (0.005, 0.005),
    "NR": (0.010, 0.010),
    "NB": (0.010, 0.010),
}

# =========================================================
# 2. Y base luminance per color
# =========================================================

Y_BASE = {
    "R":  120.0,
    "G":  150.0,
    "B":   80.0,
    "W":  200.0,
    "NR": 110.0,
    "NB":  90.0,
}

Y_VARIATION = 0.05   # ±5%

# =========================================================
# 3. xyY generator
# =========================================================

def generate_xyY(color):
    cx, cy = COLOR_XY_CENTER[color]
    dx, dy = XY_JITTER[color]

    x = np.random.uniform(cx - dx, cx + dx)
    y = np.random.uniform(cy - dy, cy + dy)

    Y0 = Y_BASE[color]
    Y = Y0 * np.random.uniform(1 - Y_VARIATION, 1 + Y_VARIATION)

    return x, y, Y

# =========================================================
# 4. Build DataFrame (NO lens)
# =========================================================

def generate_post_cal_csv(
    output_csv="Bismuth_rgbwk_per_lens_post_cal.csv",
    units=(0, 1, 2, 3),
    colors=("R", "G", "B", "W", "NR", "NB")
):
    rows = []

    for unit in units:
        for color in colors:
            x, y, Y = generate_xyY(color)

            rows.append({
                "ID": "gold",
                "sequence": "post",
                "unit_num": unit,
                "color": color,
                "x": round(x, 6),
                "y": round(y, 6),
                "Y": round(Y, 2),
            })

    df = pd.DataFrame(rows)

    # enforce column order
    COLUMN_ORDER = ["ID", "sequence", "unit_num", "color", "x", "y", "Y"]
    df = df[COLUMN_ORDER]

    df.to_csv(output_csv, index=False, encoding="utf-8-sig")
    print(f"✔ CSV generated: {output_csv}")
    print(df.head())

    return df

# =========================================================
# 5. Run
# =========================================================

if __name__ == "__main__":
    generate_post_cal_csv(
        output_csv="Bismuth_rgbwk_per_lens_post_cal.csv",
        units=(0, 1, 2, 3)
    )
