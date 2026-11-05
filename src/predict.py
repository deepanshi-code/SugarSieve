"""Prediction logic used by the app. Kept separate from the UI so it can be tested."""
import json
from functools import lru_cache

import joblib
import numpy as np
import pandas as pd

from src.data import ALL_FEATURES, PROJECT_ROOT, load_clean, train_test
from src.models import GuidelineRule

MODES = {"no_lab": "Quick measurements only", "full": "Lab results available"}
OPERATING_POINTS = {
    "matched_rate": "Standard (refers about 1 in 3 patients)",
    "high_sensitivity": "Catch more cases (refers about 1 in 2 patients)",
}
BANDS = ["Lower", "Moderate", "Higher"]


@lru_cache(maxsize=1)
def load_artifacts():
    meta = json.loads((PROJECT_ROOT / "models" / "metadata.json").read_text())
    models = {key: joblib.load(PROJECT_ROOT / info["file"]) for key, info in meta["models"].items()}
    return meta, models


@lru_cache(maxsize=1)
def input_ranges():
    """Min, median and max of each feature in the training data. The models know nothing outside these ranges."""
    train, _ = train_test(load_clean())
    stats = train[ALL_FEATURES].agg(["min", "median", "max"]).T
    return {col: (float(r["min"]), float(r["median"]), float(r["max"])) for col, r in stats.iterrows()}


def patient_frame(values):
    """One-row DataFrame from a dict. None or 0 for a measurement that can't be 0 becomes NaN (= not measured)."""
    row = {col: values.get(col) for col in ALL_FEATURES}
    df = pd.DataFrame([row], dtype=float)
    for col in ["Glucose", "BloodPressure", "SkinThickness", "Insulin", "BMI"]:
        df.loc[df[col] == 0, col] = np.nan
    return df


def risk_band(prob, thresholds):
    if prob >= thresholds["matched_rate"]:
        return "Higher"
    if prob >= thresholds["high_sensitivity"]:
        return "Moderate"
    return "Lower"


def contributions(model, X):
    """Per-feature push on the log-odds, relative to an average training patient (logistic regression only)."""
    z = model[:-1].transform(X).iloc[0]
    coef = pd.Series(model[-1].coef_[0], index=model[:-1].get_feature_names_out())
    return (coef * z).sort_values()


def assess(values, mode="no_lab", operating_point="matched_rate"):
    meta, models = load_artifacts()
    info, model = meta["models"][mode], models[mode]
    X = patient_frame(values)[info["features"]]
    prob = float(model.predict_proba(X)[0, 1])
    thresholds = info["thresholds"]
    full_row = patient_frame(values)
    return {
        "probability": prob,
        "band": risk_band(prob, thresholds),
        "refer": prob >= thresholds[operating_point],
        "guideline_refers": bool(GuidelineRule().predict(full_row)[0]) if full_row[["Age", "BMI"]].notna().all(axis=None) else None,
        "missing": [c for c in info["features"] if pd.isna(X.iloc[0][c])],
        "contributions": contributions(model, X),
        "reference": reference_patient(model),
    }


def reference_patient(model):
    """The 'average patient' the contributions are measured against: the scaler's training means."""
    scaler = model.named_steps["scale"]
    return dict(zip(scaler.feature_names_in_, scaler.mean_))
