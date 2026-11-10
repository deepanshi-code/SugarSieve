"""Export the saved models as plain numbers (JSON), plus a predictor that needs only numpy.

The .joblib files only load with the scikit-learn version that made them. A logistic regression is fully described by
a handful of numbers, so models/coefficients.json is a version-independent, human-readable copy of both models.

Usage:  python -m src.export
"""
import json

import numpy as np

from src.data import PROJECT_ROOT

COEFFICIENTS_JSON = PROJECT_ROOT / "models" / "coefficients.json"


def describe(pipeline):
    """The numbers inside one saved pipeline: impute (median) -> standardise -> logistic regression."""
    imputer, scaler, model = (pipeline.named_steps[k] for k in ["impute", "scale", "model"])
    features = list(imputer.feature_names_in_)
    return {
        "features": features,
        "medians": dict(zip(features, imputer.statistics_.round(6).tolist())),
        "means": dict(zip(features, scaler.mean_.round(6).tolist())),
        "scales": dict(zip(features, scaler.scale_.round(6).tolist())),
        "coefficients": dict(zip(features, model.coef_[0].round(6).tolist())),
        "intercept": round(float(model.intercept_[0]), 6),
    }


def predict_proba(params, X):
    """Probability of diabetes from exported numbers. X: DataFrame (or dict of columns) with the model's features."""
    f = params["features"]
    x = np.column_stack([np.asarray(X[c], dtype=float) for c in f])
    x = np.where(np.isnan(x), [params["medians"][c] for c in f], x)
    z = (x - [params["means"][c] for c in f]) / [params["scales"][c] for c in f]
    log_odds = params["intercept"] + z @ np.array([params["coefficients"][c] for c in f])
    return 1 / (1 + np.exp(-log_odds))


def export_all(path=COEFFICIENTS_JSON):
    import joblib

    meta = json.loads((PROJECT_ROOT / "models" / "metadata.json").read_text())
    out = {"note": "Logistic regression: p = 1 / (1 + exp(-(intercept + sum(coef * (x - mean) / scale)))), "
                   "with missing x replaced by the median.",
           "models": {}}
    for key, info in meta["models"].items():
        params = describe(joblib.load(PROJECT_ROOT / info["file"]))
        params["thresholds"] = info["thresholds"]
        out["models"][key] = params
    path.write_text(json.dumps(out, indent=2))
    return path


if __name__ == "__main__":
    print("saved", export_all())
