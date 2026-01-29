import pandas as pd

# =========================================================
# 1. Load pre / post calibration CSV
# =========================================================

def load_csv_safe(path):
    df = pd.read_csv(path, encoding="utf-8-sig")
    # 防止 BOM 問題
    df.columns = df.columns.str.replace('\ufeff', '')
    return df


df_pre  = load_csv_safe("Bismuth_rgbwk_per_lens.csv")
df_post = load_csv_safe("Bismuth_rgbwk_per_lens_post_cal.csv")

# =========================================================
# 2. Basic sanity check (optional but recommended)
# =========================================================

REQUIRED_COLS = ["ID", "sequence", "unit_num", "color", "x", "y", "Y"]

for name, df in [("pre", df_pre), ("post", df_post)]:
    missing = set(REQUIRED_COLS) - set(df.columns)
    if missing:
        raise ValueError(f"{name} CSV missing columns: {missing}")

# =========================================================
# 3. Concatenate pre + post
# =========================================================

df_compare = pd.concat([df_pre, df_post], ignore_index=True)

# Optional: sort for nice plotting / debugging
df_compare = df_compare.sort_values(
    by=["ID", "color", "unit_num", "sequence"]
).reset_index(drop=True)

# =========================================================
# 4. Save comparison CSV
# =========================================================

output_csv = "Bismuth_rgbwk_per_lens_pre_post_cal_comparison.csv"
df_compare.to_csv(output_csv, index=False, encoding="utf-8-sig")

print(f"✔ Pre/Post comparison CSV generated: {output_csv}")
print(df_compare.head())
