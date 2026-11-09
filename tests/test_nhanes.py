"""Checks that the NHANES validation set follows docs/external_validation_plan.md."""
import unittest

import pandas as pd

from src.nhanes import VALIDATION_CSV


class TestNhanesValidationSet(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.df = pd.read_csv(VALIDATION_CSV, index_col=0)

    def test_population_rules(self):
        self.assertTrue((self.df["Age"] >= 21).all())
        self.assertTrue(self.df["Glucose"].notna().all())  # completed OGTT

    def test_outcome_matches_definition(self):
        d = self.df
        expected = ((d.Glucose >= 200) | (d.FastingGlucose >= 126) | (d.HbA1c >= 6.5)).astype(int)
        self.assertTrue((d.Outcome == expected).all())

    def test_unavailable_inputs_are_missing(self):
        self.assertTrue(self.df["DiabetesPedigree"].isna().all())
        self.assertTrue(self.df["Insulin"].isna().all())

    def test_no_impossible_zero_blood_pressure(self):
        self.assertTrue((self.df["BloodPressure"].dropna() >= 1).all())

    def test_pregnancies_within_training_range(self):
        p = self.df["Pregnancies"].dropna()
        self.assertTrue(p.between(0, 17).all())


if __name__ == "__main__":
    unittest.main()
