"""Run with:  python -m unittest discover tests"""
import unittest

import numpy as np

from src.data import load_raw, mark_missing
from src.predict import assess, input_ranges, patient_frame, risk_band

TYPICAL = {"Pregnancies": 2, "BloodPressure": 72, "SkinThickness": 29, "BMI": 32.0,
           "DiabetesPedigree": 0.38, "Age": 40, "Glucose": 117, "Insulin": 125}


class TestCleaning(unittest.TestCase):
    def test_impossible_zeros_become_missing(self):
        df = mark_missing(load_raw())
        for col in ["Glucose", "BloodPressure", "SkinThickness", "Insulin", "BMI"]:
            self.assertFalse((df[col] == 0).any(), col)

    def test_zero_pregnancies_is_kept(self):
        self.assertTrue((mark_missing(load_raw())["Pregnancies"] == 0).any())

    def test_app_input_zero_and_none_mean_not_measured(self):
        df = patient_frame({**TYPICAL, "Insulin": 0, "SkinThickness": None, "Pregnancies": 0})
        self.assertTrue(np.isnan(df.loc[0, "Insulin"]))
        self.assertTrue(np.isnan(df.loc[0, "SkinThickness"]))
        self.assertEqual(df.loc[0, "Pregnancies"], 0)


class TestPrediction(unittest.TestCase):
    def test_probability_in_range_for_both_modes(self):
        for mode in ["no_lab", "full"]:
            p = assess(TYPICAL, mode)["probability"]
            self.assertTrue(0 < p < 1, mode)

    def test_missing_optional_values_still_predict(self):
        result = assess({**TYPICAL, "SkinThickness": None, "BloodPressure": None, "Insulin": None}, "full")
        self.assertIn("SkinThickness", result["missing"])
        self.assertTrue(0 < result["probability"] < 1)

    def test_higher_glucose_means_higher_risk(self):
        low = assess({**TYPICAL, "Glucose": 90}, "full")["probability"]
        high = assess({**TYPICAL, "Glucose": 180}, "full")["probability"]
        self.assertGreater(high, low)

    def test_no_lab_mode_ignores_lab_values(self):
        a = assess({**TYPICAL, "Glucose": 80}, "no_lab")["probability"]
        b = assess({**TYPICAL, "Glucose": 190}, "no_lab")["probability"]
        self.assertAlmostEqual(a, b)

    def test_catch_more_mode_refers_at_least_as_often(self):
        for glucose in [90, 120, 150]:
            values = {**TYPICAL, "Glucose": glucose}
            if assess(values, "full", "matched_rate")["refer"]:
                self.assertTrue(assess(values, "full", "high_sensitivity")["refer"])

    def test_guideline_rule(self):
        self.assertTrue(assess({**TYPICAL, "Age": 40, "BMI": 30})["guideline_refers"])
        self.assertFalse(assess({**TYPICAL, "Age": 30, "BMI": 40})["guideline_refers"])


class TestBands(unittest.TestCase):
    T = {"matched_rate": 0.42, "high_sensitivity": 0.28}

    def test_band_boundaries(self):
        self.assertEqual(risk_band(0.10, self.T), "Lower")
        self.assertEqual(risk_band(0.28, self.T), "Moderate")
        self.assertEqual(risk_band(0.42, self.T), "Higher")

    def test_input_ranges_match_training_data(self):
        lo, _, hi = input_ranges()["Glucose"]
        self.assertGreater(lo, 0)  # zeros were removed before computing ranges
        self.assertLess(hi, 200)


if __name__ == "__main__":
    unittest.main()
