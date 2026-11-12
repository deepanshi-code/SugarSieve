"""Tests for the Part 2 app logic."""
import unittest

from src.part2_data import cdc_ada_points, cdc_ada_risk_score
from src.part2_predict import assess_part2

PERSON = {"Age": 45, "Male": 0, "BMI": 27, "Waist": 90, "SBP": 120, "DBP": 75, "ToldHighBP": 0, "BPMeds": 0,
          "FamilyHistoryDiabetes": 0, "GestationalDiabetes": 0, "CurrentSmoker": 0, "PhysicallyActive": 1, "CVD": 0,
          "DiagnosedDiabetes": 0, "Asian": False}


class TestCdcBreakdown(unittest.TestCase):
    def test_breakdown_sums_to_score(self):
        args = ([62, 30], [1, 0], [0, 1], [1, 0], [1, 0], [0, 1], [31, 24], [False, True])
        self.assertEqual(cdc_ada_points(*args).sum(axis=1).tolist(), cdc_ada_risk_score(*args).tolist())


class TestAssessPart2(unittest.TestCase):
    def test_low_risk_person(self):
        r = assess_part2(PERSON)
        self.assertEqual(r["hba1c"]["score"], 2)                 # age 40-49 (1) + BMI 25-29 (1)
        self.assertFalse(r["hba1c"]["refer"])
        self.assertFalse(r["blood_pressure"]["measured_high"])

    def test_hba1c_follows_cdc_score(self):
        r = assess_part2({**PERSON, "Age": 62, "Male": 1, "BMI": 31, "ToldHighBP": 1, "PhysicallyActive": 0})
        self.assertEqual(r["hba1c"]["score"], 8)
        self.assertTrue(r["hba1c"]["refer"])

    def test_diagnosed_diabetes_always_gets_kidney_test_but_no_screening_hba1c(self):
        r = assess_part2({**PERSON, "Age": 25, "BMI": 22, "DiagnosedDiabetes": 1})
        self.assertTrue(r["kidney"]["refer"])
        self.assertFalse(r["hba1c"]["refer"])

    def test_new_high_blood_pressure_is_flagged(self):
        r = assess_part2({**PERSON, "SBP": 150})
        self.assertTrue(r["blood_pressure"]["new_finding"])
        self.assertTrue(r["kidney"]["kdigo_priority"])

    def test_older_age_raises_kidney_risk(self):
        young = assess_part2({**PERSON, "Age": 30})["kidney"]["risk"]
        old = assess_part2({**PERSON, "Age": 75})["kidney"]["risk"]
        self.assertGreater(old, young)

    def test_missing_answers_still_work(self):
        r = assess_part2({**PERSON, "Waist": None, "SBP": None, "DBP": None, "FamilyHistoryDiabetes": None})
        self.assertTrue(0 < r["kidney"]["risk"] < 1)


if __name__ == "__main__":
    unittest.main()
