"""Part 2 data: formulas checked against hand-calculated values, and the built dataset checked against docs/part2_plan.md."""
import unittest

import numpy as np

from src.part2_data import (PART2_CSV, TEST_CYCLES, TRAIN_CYCLES, albumin_creatinine_ratio,
                            cdc_ada_risk_score, egfr_ckd_epi_2021, load)


class TestFormulas(unittest.TestCase):
    def test_egfr_female_at_kappa(self):
        # Scr/kappa = 1, so only the age and sex terms remain: 142 x 0.9938^50 x 1.012 = 105.3
        self.assertAlmostEqual(float(egfr_ckd_epi_2021(0.7, 50, True)), 105.3, delta=0.1)

    def test_egfr_male_raised_creatinine(self):
        # 142 x (1.5/0.9)^-1.2 x 0.9938^60 = 142 x 0.5417 x 0.6886 = 53.0
        self.assertAlmostEqual(float(egfr_ckd_epi_2021(1.5, 60, False)), 53.0, delta=0.1)

    def test_egfr_falls_with_age_and_creatinine(self):
        self.assertGreater(egfr_ckd_epi_2021(1.0, 40, False), egfr_ckd_epi_2021(1.0, 70, False))
        self.assertGreater(egfr_ckd_epi_2021(0.8, 50, True), egfr_ckd_epi_2021(1.2, 50, True))

    def test_acr(self):
        self.assertEqual(float(albumin_creatinine_ratio(30, 100)), 30.0)


class TestCDCScore(unittest.TestCase):
    def score(self, **kw):
        base = dict(age=30, male=0, gestational_diabetes=0, family_history=0, told_high_bp=0,
                    physically_active=1, bmi=22, asian=False)
        base.update(kw)
        return int(cdc_ada_risk_score(*[[v] for v in base.values()])[0])

    def test_lowest_risk_is_zero(self):
        self.assertEqual(self.score(), 0)

    def test_high_risk_man(self):
        # age 62 (3) + man (1) + BMI 31 (2) + high BP (1) + inactive (1) = 8
        self.assertEqual(self.score(age=62, male=1, bmi=31, told_high_bp=1, physically_active=0), 8)

    def test_asian_bmi_cut_off(self):
        self.assertEqual(self.score(bmi=24, asian=True), 1)
        self.assertEqual(self.score(bmi=24, asian=False), 0)

    def test_missing_answers_score_zero(self):
        self.assertEqual(self.score(family_history=np.nan, physically_active=np.nan, bmi=np.nan), 0)


class TestBuiltDataset(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.df = load()

    def test_population(self):
        self.assertTrue((self.df.Age >= 20).all())

    def test_split_by_years(self):
        self.assertTrue(set(self.df[self.df.split == "train"].cycle) == set(TRAIN_CYCLES))
        self.assertTrue(set(self.df[self.df.split == "test"].cycle) == set(TEST_CYCLES))

    def test_diabetes_target_definition(self):
        d = self.df[self.df.UndxDiabetes.notna()]
        self.assertTrue(((d.HbA1c >= 6.5).astype(float) == d.UndxDiabetes).all())
        self.assertTrue((d.DiagnosedDiabetes == 0).all())

    def test_ckd_target_definition(self):
        d = self.df[self.df.UndxCKD.notna()]
        expected = ((d.eGFR < 60) | (d.ACR >= 30)).astype(float)
        self.assertTrue((expected == d.UndxCKD).all())

    def test_acr_matches_nhanes_own_ratio(self):
        d = self.df[self.df.ACR_nhanes.notna() & self.df.ACR.notna()]
        # NHANES rounds its ratio to 2 decimals, hence the small absolute tolerance
        np.testing.assert_allclose(d.ACR, d.ACR_nhanes, rtol=0.01, atol=0.01)

    def test_baselines_are_binary(self):
        for col in ["CDCHighRisk", "USPSTFRule", "KDIGOPriority"]:
            self.assertTrue(self.df[col].isin([0, 1]).all(), col)


if __name__ == "__main__":
    unittest.main()
