"""Tests for Part 2 modelling helpers: cluster-safe folds, a leak-free chain, and fold metrics."""
import unittest

import numpy as np

from src.part2_data import load
from src.part2_models import CHAIN_FEATURE, TARGETS, add_diabetes_risk, cv_splits, evaluate_fold


class TestFolds(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.train = load("train")

    def test_no_cluster_in_both_train_and_validation(self):
        for tr, va in cv_splits(self.train, "UndxDiabetes", n_repeats=1):
            shared = set(self.train.loc[tr, "cluster"]) & set(self.train.loc[va, "cluster"])
            self.assertEqual(shared, set())

    def test_every_labelled_row_validated_once_per_repeat(self):
        labelled = self.train.UndxDiabetes.notna().sum()
        seen = np.concatenate([va for _, va in cv_splits(self.train, "UndxDiabetes", n_repeats=1)])
        self.assertEqual(len(seen), labelled)
        self.assertEqual(len(set(seen)), labelled)


class TestChainHasNoLeakage(unittest.TestCase):
    def test_flipping_own_label_does_not_change_own_risk(self):
        rows = load("train")
        rows = rows[rows.cycle == "2013-2014"]          # one cycle keeps the test fast
        target = TARGETS["diabetes"]["target"]
        person = rows[rows[target] == 0].index[0]
        before, _ = add_diabetes_risk(rows, rows.iloc[:5])
        flipped = rows.copy()
        flipped.loc[person, target] = 1
        after, _ = add_diabetes_risk(flipped, rows.iloc[:5])
        self.assertAlmostEqual(before.loc[person, CHAIN_FEATURE], after.loc[person, CHAIN_FEATURE], places=12)


class TestFoldMetrics(unittest.TestCase):
    def test_metrics(self):
        y = np.array([1, 0, 1, 0, 0, 0, 0, 0, 0, 1])
        scores = np.linspace(1, 0, 10)                 # ranks people in index order
        rule = np.array([1, 1, 0, 0, 1, 0, 0, 0, 0, 0])  # refers 30 %
        m = evaluate_fold(scores, rule, rule, y)
        self.assertAlmostEqual(m["rule_rate"], 0.3)
        self.assertAlmostEqual(m["sens_at_rule_rate"], 2 / 3)  # top 3 by score: indices 0, 1, 2 -> cases 0 and 2
        self.assertAlmostEqual(m["rule_sens"], 1 / 3)          # rule refers 0, 1, 4 -> case 0 only


if __name__ == "__main__":
    unittest.main()
