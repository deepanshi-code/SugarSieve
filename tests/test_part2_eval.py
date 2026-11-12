"""Tests for the survey-design bootstrap."""
import unittest

import numpy as np

from src.part2_eval import bootstrap_indices, percentile_ci, stratum_of

# Two strata with two PSUs each; PSU sizes 3, 2, 4, 1 rows
CLUSTERS = np.array(["c_1_1"] * 3 + ["c_1_2"] * 2 + ["c_2_1"] * 4 + ["c_2_2"] * 1)


class TestBootstrap(unittest.TestCase):
    def test_stratum_parsing(self):
        self.assertEqual(list(stratum_of(["2015-2016_134_1", "2015-2016_134_2"])), ["2015-2016_134"] * 2)

    def test_each_stratum_contributes_one_psu_twice(self):
        for idx in bootstrap_indices(CLUSTERS, n_boot=50, seed=1):
            for stratum in ["c_1", "c_2"]:
                drawn = CLUSTERS[idx][stratum_of(CLUSTERS[idx]) == stratum]
                psus, counts = np.unique(drawn, return_counts=True)
                self.assertEqual(len(psus), 1)                                # one PSU per stratum
                self.assertEqual(counts[0], 2 * (CLUSTERS == psus[0]).sum())  # all its rows, twice

    def test_all_psus_get_drawn(self):
        seen = set()
        for idx in bootstrap_indices(CLUSTERS, n_boot=200, seed=2):
            seen |= set(CLUSTERS[idx])
        self.assertEqual(seen, set(CLUSTERS))

    def test_variance_of_mean_is_unbiased_for_two_psu_design(self):
        # For a stratified mean with 2 equal PSUs per stratum, Rao-Wu reproduces the textbook variance
        clusters = np.repeat([f"s{s}_{p}" for s in range(40) for p in (1, 2)], 5)
        rng = np.random.default_rng(0)
        values = rng.normal(size=len(clusters)) + np.repeat(rng.normal(size=80), 5)
        boot = [values[i].mean() for i in bootstrap_indices(clusters, n_boot=4000, seed=3)]
        psu_means = values.reshape(80, 5).mean(axis=1).reshape(40, 2)
        textbook = np.sum((psu_means[:, 0] - psu_means[:, 1]) ** 2 / 4) / 40 ** 2   # sum_h (W_h^2 * s_h^2 / n_h)
        self.assertAlmostEqual(np.var(boot) / textbook, 1.0, delta=0.15)

    def test_percentile_ci(self):
        lo, hi = percentile_ci(np.arange(1001))
        self.assertAlmostEqual(lo, 25.0)
        self.assertAlmostEqual(hi, 975.0)


if __name__ == "__main__":
    unittest.main()
