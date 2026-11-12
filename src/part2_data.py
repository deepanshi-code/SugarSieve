"""Part 2 data: NHANES 2007-2018 adults, with routine-visit inputs, targets and guideline baselines.

Every definition follows docs/part2_plan.md (section numbers in comments).
Raw files go to data/external/nhanes_raw/ (not in git). The processed dataset is data/external/part2_nhanes.csv.gz.

Usage:  python -m src.part2_data
"""
import urllib.request

import numpy as np
import pandas as pd

from src.data import PROJECT_ROOT
from src.nhanes import BASE_URL, RAW_DIR

PART2_CSV = PROJECT_ROOT / "data" / "external" / "part2_nhanes.csv.gz"
CYCLES = {"2007": "E", "2009": "F", "2011": "G", "2013": "H", "2015": "I", "2017": "J"}
TRAIN_CYCLES = ["2007-2008", "2009-2010", "2011-2012", "2013-2014"]
TEST_CYCLES = ["2015-2016", "2017-2018"]
FILES = ["DEMO", "BMX", "BPX", "BPQ", "GHB", "BIOPRO", "ALB_CR", "KIQ_U", "DIQ", "MCQ", "SMQ", "PAQ", "RHQ"]

# Model inputs (§4). DiagnosedDiabetes is used by the CKD model only.
INPUTS = ["Age", "Male", "BMI", "Waist", "SBP", "DBP", "ToldHighBP", "BPMeds", "FamilyHistoryDiabetes",
          "GestationalDiabetes", "CurrentSmoker", "PhysicallyActive", "CVD"]
CKD_INPUTS = INPUTS + ["DiagnosedDiabetes"]


# ---------------------------------------------------------------- formulas
def egfr_ckd_epi_2021(creatinine_mg_dl, age, female):
    """2021 CKD-EPI creatinine equation (no race term), as published by the National Kidney Foundation."""
    scr = np.asarray(creatinine_mg_dl, dtype=float)
    female = np.asarray(female, dtype=bool)
    kappa = np.where(female, 0.7, 0.9)
    alpha = np.where(female, -0.241, -0.302)
    ratio = scr / kappa
    return (142 * np.minimum(ratio, 1) ** alpha * np.maximum(ratio, 1) ** -1.200
            * 0.9938 ** np.asarray(age, dtype=float) * np.where(female, 1.012, 1.0))


def albumin_creatinine_ratio(albumin_mg_l, creatinine_mg_dl):
    """Urine ACR in mg/g: albumin (mg/L) / creatinine (mg/dL) x 100."""
    return np.asarray(albumin_mg_l, dtype=float) / np.asarray(creatinine_mg_dl, dtype=float) * 100


def cdc_ada_risk_score(age, male, gestational_diabetes, family_history, told_high_bp, physically_active, bmi, asian):
    """CDC/ADA Prediabetes Risk Test points (cdc.gov 'How Your Test is Scored'). High risk = 5 or more.

    A missing answer scores 0 points for that item (documented in the Part 2 plan change log).
    """
    def yes(x):
        # as int: adding boolean arrays would give logical OR, not a count of points
        return (pd.Series(x) == 1).to_numpy().astype(int)

    age = np.asarray(age, dtype=float)
    bmi = np.asarray(bmi, dtype=float)
    low = np.where(np.asarray(asian, dtype=bool), 23, 25)          # Asian cut-off for the first band
    points = np.select([age >= 60, age >= 50, age >= 40], [3, 2, 1], 0)
    points += yes(male) + yes(gestational_diabetes) + yes(family_history) + yes(told_high_bp)
    points += (pd.Series(physically_active) == 0).to_numpy().astype(int)  # not active = 1 point
    points += np.select([bmi >= 40, bmi >= 30, bmi >= low], [3, 2, 1], 0)  # NaN BMI -> 0 points
    return points


# ---------------------------------------------------------------- download and build
def download_all(raw_dir=RAW_DIR):
    raw_dir.mkdir(parents=True, exist_ok=True)
    for year, suffix in CYCLES.items():
        for name in FILES:
            target = raw_dir / f"{name}_{suffix}.xpt"
            if not target.exists():
                urllib.request.urlretrieve(BASE_URL.format(year=year, name=name, suffix=suffix), target)


def _read(name, suffix, raw_dir):
    return pd.read_sas(raw_dir / f"{name}_{suffix}.xpt", format="xport").set_index("SEQN")


def _yes_no(series):
    """NHANES 1 = yes, 2 = no; refused / don't know (7, 9, 77, 99) -> missing."""
    return series.map({1: 1.0, 2: 0.0})


def _mean_reading(frame):
    # SAS transport stores 0 as a tiny float; a reading of 0 means "not obtained"
    return frame.where(frame >= 1).mean(axis=1)


def build(raw_dir=RAW_DIR):
    frames = []
    for year, s in CYCLES.items():
        r = {name: _read(name, s, raw_dir) for name in FILES}
        d = r["DEMO"][["RIAGENDR", "RIDAGEYR", "RIDRETH1", "RIDEXPRG", "RIDSTATR", "WTMEC2YR", "SDMVPSU", "SDMVSTRA"]].copy()
        d["RIDRETH3"] = r["DEMO"]["RIDRETH3"] if "RIDRETH3" in r["DEMO"] else np.nan
        cols = {"BMX": ["BMXBMI", "BMXWAIST"], "BPX": ["BPXSY1", "BPXSY2", "BPXSY3", "BPXDI1", "BPXDI2", "BPXDI3"],
                "BPQ": ["BPQ020", "BPQ040A", "BPQ050A"], "GHB": ["LBXGH"], "BIOPRO": ["LBXSCR"],
                "ALB_CR": ["URXUMA", "URXUCR", "URDACT"], "KIQ_U": ["KIQ022"], "DIQ": ["DIQ010"],
                "MCQ": ["MCQ300C", "MCQ160B", "MCQ160C", "MCQ160D", "MCQ160E", "MCQ160F"], "SMQ": ["SMQ020", "SMQ040"],
                "PAQ": ["PAQ605", "PAQ620", "PAQ635", "PAQ650", "PAQ665"], "RHQ": ["RHQ131", "RHQ162"]}
        for name, c in cols.items():
            d = d.join(r[name].reindex(columns=c), how="left")
        d["cycle"] = f"{year}-{int(year) + 1}"
        frames.append(d)
    d = pd.concat(frames)

    # Population (§2): adults 20+, examined, not pregnant
    d = d[(d.RIDAGEYR >= 20) & (d.RIDSTATR == 2) & (d.RIDEXPRG != 1)]

    female = d.RIAGENDR == 2
    out = pd.DataFrame(index=d.index)
    out["cycle"] = d.cycle
    out["split"] = np.where(d.cycle.isin(TRAIN_CYCLES), "train", "test")
    out["cluster"] = d.cycle + "_" + d.SDMVSTRA.astype(int).astype(str) + "_" + d.SDMVPSU.astype(int).astype(str)
    out["weight"] = d.WTMEC2YR
    out["race"] = d.RIDRETH1.map({1: "Mexican American", 2: "Other Hispanic", 3: "Non-Hispanic White",
                                  4: "Non-Hispanic Black", 5: "Other / multiracial"})
    out.loc[d.RIDRETH3 == 6, "race"] = "Non-Hispanic Asian"   # identified separately from 2011
    asian = (d.RIDRETH3 == 6).to_numpy()

    # Inputs (§4)
    out["Age"] = d.RIDAGEYR
    out["Male"] = (~female).astype(float)
    out["BMI"] = d.BMXBMI
    out["Waist"] = d.BMXWAIST
    out["SBP"] = _mean_reading(d[["BPXSY1", "BPXSY2", "BPXSY3"]])
    out["DBP"] = _mean_reading(d[["BPXDI1", "BPXDI2", "BPXDI3"]])
    out["ToldHighBP"] = _yes_no(d.BPQ020)
    meds = _yes_no(d.BPQ050A)
    out["BPMeds"] = meds.where(meds.notna() | ~((d.BPQ020 == 2) | (d.BPQ040A == 2)), 0.0)  # not told / not prescribed -> 0
    out["FamilyHistoryDiabetes"] = _yes_no(d.MCQ300C)
    gdm = _yes_no(d.RHQ162).where(d.RHQ131 != 2, 0.0)          # never pregnant -> no gestational diabetes
    out["GestationalDiabetes"] = np.where(female, gdm, 0.0)
    ever = _yes_no(d.SMQ020)
    out["CurrentSmoker"] = np.where(ever == 0, 0.0, np.where(d.SMQ040.isin([1, 2]), 1.0,
                                    np.where(d.SMQ040 == 3, 0.0, np.nan)))
    pa = d[["PAQ605", "PAQ620", "PAQ635", "PAQ650", "PAQ665"]].apply(_yes_no)
    out["PhysicallyActive"] = np.where((pa == 1).any(axis=1), 1.0, np.where((pa == 0).all(axis=1), 0.0, np.nan))
    cvd = d[["MCQ160B", "MCQ160C", "MCQ160D", "MCQ160E", "MCQ160F"]].apply(_yes_no)
    out["CVD"] = np.where((cvd == 1).any(axis=1), 1.0, np.where((cvd == 0).all(axis=1), 0.0, np.nan))
    out["DiagnosedDiabetes"] = (d.DIQ010 == 1).astype(float)

    # Lab values (targets only, never inputs)
    out["HbA1c"] = d.LBXGH
    out["eGFR"] = egfr_ckd_epi_2021(d.LBXSCR, d.RIDAGEYR, female)
    out["ACR"] = albumin_creatinine_ratio(d.URXUMA, d.URXUCR)
    out["ACR_nhanes"] = d.URDACT  # NHANES's own ratio (2009+), kept only to check the calculation

    # Targets (§3); NaN = not in that target's population or not measured
    out["UndxDiabetes"] = np.where((d.DIQ010 != 1) & out.HbA1c.notna(), (out.HbA1c >= 6.5).astype(float), np.nan)
    out["UndxDysglycemia"] = np.where((d.DIQ010 != 1) & out.HbA1c.notna(), (out.HbA1c >= 5.7).astype(float), np.nan)
    low_egfr, high_acr = out.eGFR < 60, out.ACR >= 30
    both_measured = out.eGFR.notna() & out.ACR.notna()
    ckd = np.where(low_egfr | high_acr, 1.0, np.where(both_measured, 0.0, np.nan))  # positive if any marker abnormal
    out["UndxCKD"] = np.where(d.KIQ022 != 1, ckd, np.nan)

    # Hypertension, the connecting condition (§1, §5)
    out["HighBPMeasured"] = np.where(out.SBP.notna() | out.DBP.notna(),
                                     ((out.SBP >= 140) | (out.DBP >= 90)).astype(float), np.nan)
    out["Hypertension"] = ((out.ToldHighBP == 1) | (out.BPMeds == 1) | (out.HighBPMeasured == 1)).astype(float)

    # Baselines (§5)
    out["CDCScore"] = cdc_ada_risk_score(out.Age, out.Male, out.GestationalDiabetes, out.FamilyHistoryDiabetes,
                                         out.ToldHighBP, out.PhysicallyActive, out.BMI, asian)
    out["CDCHighRisk"] = (out.CDCScore >= 5).astype(float)
    out["USPSTFRule"] = (out.Age.between(35, 70) & (out.BMI >= 25)).astype(float)
    out["KDIGOPriority"] = ((out.Hypertension == 1) | (out.DiagnosedDiabetes == 1) | (out.CVD == 1)).astype(float)
    return out


def load(split=None):
    df = pd.read_csv(PART2_CSV, index_col=0)
    return df if split is None else df[df.split == split]


if __name__ == "__main__":
    download_all()
    PART2_CSV.parent.mkdir(parents=True, exist_ok=True)
    build().to_csv(PART2_CSV)
    print("saved", PART2_CSV)
