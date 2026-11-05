"""Model pipelines, baselines and the screening metric shared by the notebooks and the app.

All preprocessing (log transform, imputation, scaling) lives *inside* the pipelines,
so during cross-validation it is fitted on the training folds only (no leakage),
and the saved model applies exactly the same steps to new patients in the app.
"""
import numpy as np
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.experimental import enable_iterative_imputer  # noqa: F401  (activates IterativeImputer)
from sklearn.impute import IterativeImputer, SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, StandardScaler

SKEWED = ["Insulin", "DiabetesPedigree", "SkinThickness"]
RANDOM_STATE = 42


# ---------------------------------------------------------------- baselines
class GuidelineRule(BaseEstimator, ClassifierMixin):
    """Refer if Age >= 35 and BMI >= 25 (based on USPSTF 2021 screening criteria). Learns nothing."""

    def fit(self, X, y):
        self.classes_ = np.array([0, 1])
        return self

    def predict(self, X):
        return ((X["Age"] >= 35) & (X["BMI"] >= 25)).astype(int).to_numpy()

    def predict_proba(self, X):
        p = self.predict(X).astype(float)
        return np.column_stack([1 - p, p])


# ---------------------------------------------------------------- pipelines
def _log_skewed(features):
    """log1p for the skewed columns that are part of this feature set; other columns pass through."""
    skewed = [c for c in SKEWED if c in features]
    return ColumnTransformer(
        [("log", FunctionTransformer(np.log1p, feature_names_out="one-to-one"), skewed)],
        remainder="passthrough",
        verbose_feature_names_out=False,
    )


def logistic(features, log_transform=False, imputer="median", add_indicator=False, C=1.0, class_weight=None):
    if imputer == "median":
        imp = SimpleImputer(strategy="median", add_indicator=add_indicator)
    else:
        imp = IterativeImputer(random_state=RANDOM_STATE, add_indicator=add_indicator)
    steps = [("log", _log_skewed(features))] if log_transform else []
    steps += [
        ("impute", imp),
        ("scale", StandardScaler()),
        ("model", LogisticRegression(C=C, class_weight=class_weight, max_iter=1000)),
    ]
    return Pipeline(steps).set_output(transform="pandas")


def random_forest(features):
    return Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("model", RandomForestClassifier(n_estimators=300, min_samples_leaf=5,
                                         random_state=RANDOM_STATE, n_jobs=-1)),
    ])


def gradient_boosting(features, learning_rate=0.05, max_depth=3):
    # Handles missing values natively, so no imputer is needed
    return Pipeline([
        ("model", HistGradientBoostingClassifier(learning_rate=learning_rate, max_depth=max_depth,
                                                 max_iter=200,
                                                 random_state=RANDOM_STATE)),
    ])


# ---------------------------------------------------------------- metrics
def sensitivity_at_rate(y_true, scores, rate):
    """Share of diabetes cases caught if we refer the top `rate` fraction of patients by score."""
    y_true = np.asarray(y_true)
    k = int(round(rate * len(scores)))
    referred = np.argsort(-np.asarray(scores), kind="stable")[:k]
    return y_true[referred].sum() / y_true.sum()


def threshold_for_rate(scores, rate):
    """Score cut-off that refers roughly the top `rate` fraction of patients."""
    return float(np.quantile(scores, 1 - rate))
