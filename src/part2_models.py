"""Part 2 modelling: candidate models, cluster-aware cross-validation, the diabetes -> kidney "chain", and evaluation.

Kept in src/ (not only in notebooks) so it can be tested and reused by the final evaluation and the app.
"""
import numpy as np
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.model_selection import GroupKFold, StratifiedGroupKFold

from src.models import gradient_boosting, logistic, sensitivity_at_rate
from src.part2_data import CKD_INPUTS, INPUTS

TARGETS = {
    "diabetes": {"target": "UndxDiabetes", "features": INPUTS, "rule": "CDCHighRisk", "rule_score": "CDCScore"},
    "ckd": {"target": "UndxCKD", "features": CKD_INPUTS, "rule": "KDIGOPriority", "rule_score": "KDIGOPriority"},
}
CHAIN_FEATURE = "DiabetesRisk"
MODEL_KINDS = {"Logistic regression": logistic, "Gradient boosting": gradient_boosting}


def cv_splits(df, target, n_splits=5, n_repeats=3, seed=42):
    """Stratified folds that keep each NHANES sampling cluster in one fold (people in a cluster aren't independent)."""
    rows = df[df[target].notna()]
    splits = []
    for r in range(n_repeats):
        cv = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=seed + r)
        for tr, va in cv.split(rows, rows[target], groups=rows["cluster"]):
            splits.append((rows.index[tr], rows.index[va]))
    return splits


def add_diabetes_risk(fit_rows, predict_rows, kind=logistic, inner_splits=5, seed=0):
    """The chain input: predicted diabetes risk, without leakage.

    predict_rows get a diabetes model fitted on all of fit_rows. fit_rows themselves get out-of-fold
    predictions (inner cross-validation), so no row's risk comes from a model that saw its own label.
    Returns (fit_rows, predict_rows) copies with a DiabetesRisk column.
    """
    feats, target = TARGETS["diabetes"]["features"], TARGETS["diabetes"]["target"]
    fit_rows, predict_rows = fit_rows.copy(), predict_rows.copy()
    labelled = fit_rows[fit_rows[target].notna()]
    predict_rows[CHAIN_FEATURE] = kind(feats).fit(labelled[feats], labelled[target]).predict_proba(predict_rows[feats])[:, 1]

    fit_rows[CHAIN_FEATURE] = np.nan
    # Folds depend on sampling clusters only, never on labels, so a person's own label can't affect
    # which model predicts them
    cv = GroupKFold(n_splits=inner_splits, shuffle=True, random_state=seed)
    for tr, va in cv.split(fit_rows, groups=fit_rows["cluster"]):
        inner = fit_rows.iloc[tr]
        inner = inner[inner[target].notna()]
        model = kind(feats).fit(inner[feats], inner[target])
        fit_rows.iloc[va, fit_rows.columns.get_loc(CHAIN_FEATURE)] = model.predict_proba(fit_rows.iloc[va][feats])[:, 1]
    return fit_rows, predict_rows


def evaluate_fold(model_scores, rule, rule_score, y):
    """Metrics for one validation fold: model vs the guideline baseline, at the baseline's referral rate."""
    rate = float(np.mean(rule))
    return {
        "roc_auc": roc_auc_score(y, model_scores),
        "pr_auc": average_precision_score(y, model_scores),
        "sens_at_rule_rate": sensitivity_at_rate(y, model_scores, rate),
        "rule_sens": sensitivity_at_rate(y, rule.astype(float), rate),
        "rule_roc_auc": roc_auc_score(y, rule_score),
        "rule_rate": rate,
    }
