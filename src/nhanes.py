"""Download NHANES files used for external validation.

NHANES (US National Health and Nutrition Examination Survey, CDC/NCHS) is public-domain data.
Cycles 2005-2006 to 2015-2016 include an oral glucose tolerance test (OGTT) in a fasting subsample.
Raw files are saved to data/external/nhanes_raw/ (not committed to git).

Usage:  python -m src.nhanes
"""
import urllib.request

from src.data import PROJECT_ROOT

RAW_DIR = PROJECT_ROOT / "data" / "external" / "nhanes_raw"
BASE_URL = "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/{year}/DataFiles/{name}_{suffix}.xpt"
CYCLES = {"2005": "D", "2007": "E", "2009": "F", "2011": "G", "2013": "H", "2015": "I"}
FILES = ["DEMO", "OGTT", "GLU", "GHB", "BMX", "BPX", "RHQ", "MCQ", "DIQ"]


def download_all(raw_dir=RAW_DIR):
    raw_dir.mkdir(parents=True, exist_ok=True)
    for year, suffix in CYCLES.items():
        for name in FILES:
            target = raw_dir / f"{name}_{suffix}.xpt"
            if target.exists():
                continue
            url = BASE_URL.format(year=year, name=name, suffix=suffix)
            urllib.request.urlretrieve(url, target)
            print("downloaded", target.name)
    return raw_dir


VALIDATION_CSV = PROJECT_ROOT / "data" / "external" / "nhanes_validation.csv"


def _read(name, suffix, raw_dir):
    import pandas as pd

    return pd.read_sas(raw_dir / f"{name}_{suffix}.xpt", format="xport").set_index("SEQN")


def build_validation_set(raw_dir=RAW_DIR):
    """One row per eligible woman, with model inputs and the outcome, as defined in docs/external_validation_plan.md."""
    import numpy as np
    import pandas as pd

    frames = []
    for year, s in CYCLES.items():
        r = {name: _read(name, s, raw_dir) for name in FILES}
        df = r["DEMO"][["RIAGENDR", "RIDAGEYR", "RIDEXPRG"]].join(r["OGTT"][["LBXGLT"]], how="inner")
        for name, cols in [("GLU", ["LBXGLU"]), ("GHB", ["LBXGH"]), ("BMX", ["BMXBMI", "BMXTRI"]),
                           ("BPX", ["BPXDI1", "BPXDI2", "BPXDI3"]), ("RHQ", ["RHQ131", "RHQ160"]),
                           ("MCQ", ["MCQ300C"]), ("DIQ", ["DIQ010"])]:
            df = df.join(r[name].reindex(columns=cols), how="left")
        df["cycle"] = f"{year}-{int(year) + 1}"
        frames.append(df)
    d = pd.concat(frames)

    # Population (plan, "Population")
    d = d[(d.RIAGENDR == 2) & (d.RIDAGEYR >= 21) & (d.RIDEXPRG != 1) & (d.DIQ010 != 1) & d.LBXGLT.notna()]

    # Model inputs (plan, "Features")
    # SAS transport files store 0 as a tiny float (~5e-79), so "0 = unmeasurable" is caught with < 1
    bp_readings = d[["BPXDI1", "BPXDI2", "BPXDI3"]]
    bp = bp_readings.where(bp_readings >= 1).mean(axis=1)
    preg = d.RHQ160.where(d.RHQ160 < 77)                      # 77/99 = refused / don't know
    preg = preg.where(d.RHQ131 != 2, 0).clip(upper=17)        # never pregnant -> 0
    out = pd.DataFrame({
        "Pregnancies": preg,
        "BloodPressure": bp,
        "SkinThickness": d.BMXTRI,
        "BMI": d.BMXBMI,
        "DiabetesPedigree": np.nan,                           # not available in NHANES
        "Age": d.RIDAGEYR,
        "Glucose": d.LBXGLT,                                  # 2-hour OGTT glucose
        "Insulin": np.nan,                                    # 2-hour insulin not available
        "FastingGlucose": d.LBXGLU,
        "HbA1c": d.LBXGH,
        "FamilyHistory": d.MCQ300C.map({1: 1, 2: 0}),         # 7/9 -> missing
        "cycle": d.cycle,
    })
    # Outcome: undiagnosed diabetes by lab criteria (plan, "Outcome")
    out["Outcome"] = ((out.Glucose >= 200) | (out.FastingGlucose >= 126) | (out.HbA1c >= 6.5)).astype(int)
    return out


if __name__ == "__main__":
    download_all()
    VALIDATION_CSV.parent.mkdir(parents=True, exist_ok=True)
    build_validation_set().to_csv(VALIDATION_CSV)
    print("saved", VALIDATION_CSV)
