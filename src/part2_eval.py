"""Part 2 evaluation helpers: a survey-design bootstrap for confidence intervals.

NHANES samples people in clusters (PSUs) within strata, so people are not independent. Confidence intervals resample
whole PSUs within each stratum. With 2 PSUs per stratum (every test-year stratum), the naive "draw 2 of 2 with
replacement" bootstrap understates variance by half. So we use the Rao-Wu rescaling bootstrap with m = n - 1: draw
one PSU per stratum and count it twice. That is unbiased for the variance of linear statistics.
"""
import numpy as np


def stratum_of(cluster_ids):
    """Cluster ids look like 'cycle_stratum_psu'; the stratum is everything before the last underscore."""
    return np.array([c.rsplit("_", 1)[0] for c in cluster_ids])


def bootstrap_indices(cluster_ids, n_boot=5000, seed=42):
    """Yield arrays of row positions, one resample at a time (Rao-Wu, m = n - 1)."""
    cluster_ids = np.asarray(cluster_ids)
    strata = stratum_of(cluster_ids)
    rows_of = {c: np.flatnonzero(cluster_ids == c) for c in np.unique(cluster_ids)}
    psus_in = {s: np.unique(cluster_ids[strata == s]) for s in np.unique(strata)}
    rng = np.random.default_rng(seed)
    for _ in range(n_boot):
        picks = []
        for psus in psus_in.values():
            n = len(psus)
            if n == 1:                                   # nothing to resample
                picks.append(rows_of[psus[0]])
            elif n == 2:                                 # Rao-Wu m = 1: pick one PSU, count it twice
                chosen = rows_of[psus[rng.integers(0, 2)]]
                picks.extend([chosen, chosen])
            else:                                        # fallback for larger strata: n draws with replacement
                picks.extend(rows_of[p] for p in rng.choice(psus, size=n, replace=True))
        yield np.concatenate(picks)


def percentile_ci(values, level=0.95):
    values = np.asarray(values, dtype=float)
    values = values[~np.isnan(values)]
    lo, hi = np.percentile(values, [(1 - level) / 2 * 100, (1 + level) / 2 * 100])
    return float(lo), float(hi)
