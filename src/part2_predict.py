"""Part 2 prediction logic for the app: which blood tests does this person need?

Follows the Part 2 results (notebook 12):
- HbA1c: the official CDC/ADA risk score decides, because the model was not better than it. The model's risk is shown
  for information only, with a warning for Asian American adults, whose risk the model underestimates.
- Kidney panel: the kidney model decides (it beat the KDIGO priority groups). People with diagnosed diabetes are always
  referred, because ADA and KDIGO recommend yearly kidney screening for them.
"""
import json
from functools import lru_cache

import joblib
import numpy as np
import pandas as pd

from src.data import PROJECT_ROOT
from src.part2_data import CKD_INPUTS, INPUTS, cdc_ada_points

PART2_DIR = PROJECT_ROOT / "models" / "part2"


@lru_cache(maxsize=1)
def load_part2():
    meta = json.loads((PART2_DIR / "metadata.json").read_text())
    models = {k: joblib.load(PROJECT_ROOT / v["file"]) for k, v in meta["models"].items()}
    return meta, models


def assess_part2(values):
    """values: dict with the model inputs (see src.part2_data.INPUTS / CKD_INPUTS) plus 'Asian' (bool).
    Missing or unknown answers can be None."""
    meta, models = load_part2()
    X = pd.DataFrame([{c: values.get(c) for c in CKD_INPUTS}], dtype=float)
    v = X.iloc[0]

    points = cdc_ada_points([v.Age], [v.Male], [v.GestationalDiabetes], [v.FamilyHistoryDiabetes], [v.ToldHighBP],
                            [v.PhysicallyActive], [v.BMI], [bool(values.get("Asian"))]).iloc[0]
    score = int(points.sum())
    diabetes_risk = float(models["diabetes"].predict_proba(X[INPUTS])[0, 1])
    kidney_risk = float(models["ckd"].predict_proba(X[meta["models"]["ckd"]["features"]])[0, 1])
    kidney_threshold = meta["models"]["ckd"]["thresholds"]["matched_rate"]

    measured_high = bool((v.SBP >= 140) or (v.DBP >= 90))
    hypertension = bool(v.ToldHighBP == 1 or v.BPMeds == 1 or measured_high)
    diagnosed = bool(v.DiagnosedDiabetes == 1)
    kdigo = hypertension or diagnosed or v.CVD == 1

    return {
        "diagnosed_diabetes": diagnosed,
        "hba1c": {"refer": (not diagnosed) and score >= 5, "score": score, "points": points.to_dict(),
                  "model_risk": diabetes_risk, "asian_warning": bool(values.get("Asian"))},
        "kidney": {"refer": diagnosed or kidney_risk >= kidney_threshold, "risk": kidney_risk,
                   "threshold": kidney_threshold, "because_diagnosed_diabetes": diagnosed and kidney_risk < kidney_threshold,
                   "kdigo_priority": bool(kdigo)},
        "blood_pressure": {"measured_high": measured_high, "known": bool(v.ToldHighBP == 1),
                           "new_finding": measured_high and v.ToldHighBP != 1, "sbp": v.SBP, "dbp": v.DBP},
    }
