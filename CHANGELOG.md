# Changelog

## v1.0.0 (2026-11-13): complete project

### Part 2: one visit, three connected conditions
- **Plan** written and committed before any outcome was examined ([docs/part2_plan.md](docs/part2_plan.md)). Baselines and formulas were
  verified from source documents: the CDC/ADA risk test, the KDIGO 2024 priority groups, and the CKD-EPI 2021 equation.
- **Data pipeline** for NHANES 2007–2018 (`src/part2_data.py`) and a training-years audit (notebook 10). A test against hand-calculated values
  caught a scoring bug (adding true/false arrays acts as logical OR), which was fixed before any modelling.
- **Modelling** on 2007–2014 with cluster-aware cross-validation (notebook 11). A label-flip test caught a leakage weakness in the chain's fold
  assignment, which was fixed.
- **Bootstrap corrected** before the test years were examined: Rao–Wu rescaling for strata with two sampling units.
- **One-time evaluation** on 2015–2018 (notebook 12). The kidney model beats KDIGO; the diabetes model does not beat the CDC/ADA score.
  Fairness, interconnection, survey-weighted and eGFR-only analyses.
- **App page "Which blood tests?"**, with the app split into two pages, plus the [Part 2 report](docs/part2_report.md) and model-card section.

### Part 1: who should get a glucose test?
- Problem definition with success criteria fixed before modelling; data audit (zeros used as missing values); modelling with repeated CV;
  a one-time test with bootstrap CIs (notebooks 01–03).
- Exploratory age-subgroup analysis (notebook 04).
- **External validation** on 5,298 NHANES women, following a plan committed before outcomes were examined (notebook 05).
- Sensitivity check with the guideline rule capped at age 70 (notebook 06).
- Streamlit app, deployed at [sugarsieve.streamlit.app](https://sugarsieve.streamlit.app/); report, model card, and version-independent model
  export (`models/coefficients.json`).

### Engineering
- GitHub Actions run all tests on every push: formulas, data definitions, leakage, the bootstrap, model reproduction, and both app pages.
- Colour-blind-safe chart colours; the app layout works on phones.
- MIT License for the code; data keeps its original terms.
