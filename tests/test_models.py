"""Tests for the metrics, the baseline rule, and that the saved models reproduce the reported results."""
import json
import unittest

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from src.data import PROJECT_ROOT, TARGET, load_clean, train_test
from src.export import COEFFICIENTS_JSON, predict_proba
from src.models import GuidelineRule, logistic, sensitivity_at_rate, threshold_for_rate

META = json.loads((PROJECT_ROOT / "models" / "metadata.json").read_text())
MODELS = {k: joblib.load(PROJECT_ROOT / v["file"]) for k, v in META["models"].items()}


class TestMetrics(unittest.TestCase):
    def test_sensitivity_at_rate_refers_top_scores(self):
        y = [1, 0, 1, 0]
        scores = [0.9, 0.8, 0.1, 0.2]
        self.assertEqual(sensitivity_at_rate(y, scores, 0.5), 0.5)  # refers 0.9 and 0.8: one of two cases
        self.assertEqual(sensitivity_at_rate(y, scores, 1.0), 1.0)
        self.assertEqual(sensitivity_at_rate(y, scores, 0.0), 0.0)

    def test_perfect_ranking_catches_all_cases_at_their_rate(self):
        y = np.array([0] * 70 + [1] * 30)
        self.assertEqual(sensitivity_at_rate(y, y.astype(float), 0.3), 1.0)

    def test_threshold_for_rate_refers_about_that_share(self):
        scores = np.random.default_rng(0).random(10_000)
        for rate in [0.1, 0.33, 0.5]:
            self.assertAlmostEqual((scores >= threshold_for_rate(scores, rate)).mean(), rate, delta=0.01)


class TestGuidelineRule(unittest.TestCase):
    X = pd.DataFrame({"Age": [30, 40, 40, 75], "BMI": [40, 24, 30, 30]})

    def test_rule(self):
        self.assertEqual(GuidelineRule().predict(self.X).tolist(), [0, 0, 1, 1])

    def test_upper_age_limit(self):
        self.assertEqual(GuidelineRule(max_age=70).predict(self.X).tolist(), [0, 0, 1, 0])


class TestSavedModelsReproduce(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.train, cls.test = train_test(load_clean())

    def test_refitting_gives_the_saved_coefficients(self):
        for key, info in META["models"].items():
            refit = logistic(info["features"]).fit(self.train[info["features"]], self.train[TARGET])
            np.testing.assert_allclose(refit[-1].coef_, MODELS[key][-1].coef_, atol=1e-8, err_msg=key)

    def test_reported_test_set_roc_auc(self):
        # Values reported in docs/report.md and notebook 03
        for key, expected in [("no_lab", 0.730), ("full", 0.813)]:
            f = META["models"][key]["features"]
            auc = roc_auc_score(self.test[TARGET], MODELS[key].predict_proba(self.test[f])[:, 1])
            self.assertAlmostEqual(auc, expected, places=3, msg=key)

    def test_exported_json_matches_saved_models(self):
        params = json.loads(COEFFICIENTS_JSON.read_text())["models"]
        for key, info in META["models"].items():
            f = info["features"]
            np.testing.assert_allclose(predict_proba(params[key], self.test),
                                       MODELS[key].predict_proba(self.test[f])[:, 1], atol=1e-5, err_msg=key)


if __name__ == "__main__":
    unittest.main()
