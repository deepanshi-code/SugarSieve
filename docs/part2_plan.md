# SugarSieve Part 2: one visit, three connected conditions (problem definition and pre-registered plan)

*Written and committed **before** any Part 2 outcome (HbA1c, kidney tests) was examined. Only file and variable availability were
checked. Changes after results are seen must be logged at the bottom with a reason.*

## 1. Problem
Type 2 diabetes, high blood pressure and chronic kidney disease (CKD) share causes and often occur together. Diabetes and hypertension are
the leading causes of CKD. All three are frequently **undiagnosed**. Diabetes needs a blood test (HbA1c) and CKD needs a blood and urine test
(creatinine and urine albumin), but blood pressure is measured at the visit itself.

**Question:** after one routine clinic visit (questions, weight, waist, blood pressure), **which blood tests does this person need?**
- an **HbA1c** test, for undiagnosed diabetes;
- a **kidney panel** (creatinine and urine albumin), for undiagnosed CKD.

**Why blood pressure isn't a target:** it's measured at the visit, so "predicting" it would be circular. Instead, measured and known
hypertension are **inputs**, and the three-way overlap is studied directly (§7.3).

**Relation to Part 1:** Part 1 (Pima, notebooks 01–06) studied diabetes alone, with inputs clinics don't routinely collect (skinfold,
pedigree score) and an outdated test (OGTT). Part 2 uses routine inputs, current tests, modern data, an official risk questionnaire as
the baseline, and a validation on later years.

## 2. Data
NHANES (CDC/NCHS, public domain), cycles **2007–2008 to 2017–2018**. 2005–2006 is excluded because it lacks the physical-activity and
gestational-diabetes questions that the CDC/ADA risk test needs.
- **Training:** 2007–2014 (4 cycles). **Test (temporal validation):** 2015–2018 (2 cycles), used **once**.
- Adults aged **20+** who had the examination, and **not pregnant**. Men and women.

## 3. Targets
| Target | Population | Positive if | Source |
|---|---|---|---|
| **Undiagnosed diabetes** | Never told they have diabetes (`DIQ010` ≠ 1) | HbA1c ≥ 6.5 % (`LBXGH`) | Standard diagnostic HbA1c threshold |
| **Undiagnosed CKD markers** | Never told they have weak/failing kidneys (`KIQ022` ≠ 1) | eGFR < 60 mL/min/1.73 m² **or** urine albumin-to-creatinine ratio ≥ 30 mg/g | KDIGO 2024 categories G3–G5 / A2–A3 |

- **eGFR** uses the **2021 CKD-EPI creatinine equation** (no race term), as published by the National Kidney Foundation:
  eGFR = 142 × min(Scr/κ, 1)^α × max(Scr/κ, 1)^−1.200 × 0.9938^age × 1.012 [if female]; κ = 0.7 (F) / 0.9 (M); α = −0.241 (F) / −0.302 (M).
- **ACR** = urine albumin (`URXUMA`, mg/L) ÷ urine creatinine (`URXUCR`, mg/dL) × 100, in mg/g. It's computed for every cycle because
  the ready-made variable is missing in 2007–08.
- KDIGO defines CKD as abnormalities **present for at least 3 months**, and NHANES measures once. So the target is *laboratory evidence
  of CKD on a single test*, which overstates true CKD somewhat (limitation).
- HbA1c is used rather than fasting glucose because it was measured in **everyone**, not just a fasting subsample.
- **Secondary diabetes target:** HbA1c ≥ 5.7 % (prediabetes or diabetes), because the CDC/ADA test was designed for prediabetes.

## 4. Inputs (routine visit only, no blood or urine tests)
Age; sex; BMI; waist circumference; mean measured systolic and diastolic BP (`BPXSY1–3`, `BPXDI1–3`, readings of 0 treated as missing);
told high BP (`BPQ020`); taking BP medication (`BPQ050A`); family history of diabetes (`MCQ300C`); gestational diabetes (`RHQ162`, women);
current smoker (`SMQ020`/`SMQ040`); physically active (any vigorous/moderate work or leisure activity, or walking/cycling:
`PAQ605/620/635/650/665`); history of cardiovascular disease (any of `MCQ160B–F`: heart failure, coronary disease, angina, heart attack,
stroke). For the CKD target only, also **diagnosed diabetes** (`DIQ010`), the strongest known CKD risk factor.

**Race/ethnicity is not a model input.** Using race in clinical risk equations is contested (the 2021 CKD-EPI equation removed it). It is
used only to **check fairness** (§7.4).

## 5. Baselines (official, verified sources)
| Target | Baseline | Source (checked) |
|---|---|---|
| Diabetes (primary) | **CDC/ADA Prediabetes Risk Test, score ≥ 5**: age <40 / 40–49 / 50–59 / 60+ = 0/1/2/3; man = 1; woman with gestational diabetes = 1; family history = 1; told high BP = 1; not physically active = 1; BMI <25 / 25–29 / 30–39 / 40+ = 0/1/2/3 (Asian: <23 / 23–29) | [CDC "How Your Test is Scored"](https://www.cdc.gov/diabetes/widgets/risktest/how-your-test-is-scored.html) |
| Diabetes (secondary) | Part 1's rule: age 35–70 and BMI ≥ 25 | Based on USPSTF 2021 |
| CKD | **KDIGO priority groups:** known or measured hypertension (told, on medication, or mean ≥ 140/90), **or** diagnosed diabetes, **or** cardiovascular disease | KDIGO 2024 guideline, Kidney Int 105(4S), p. S170: "The highest priority conditions for CKD detection are hypertension, diabetes, and CVD" |

Notes: the CDC test was designed for prediabetes, so it's used for diabetes as the standard public screening tool (limitation). Asian
BMI cut-offs apply from 2011, when NHANES first identifies Asian participants separately (`RIDRETH3`).

## 6. Models
- Separate models per target. **Logistic regression** (median imputation, scaling; as in Part 1) is the primary model. Gradient boosting
  is compared in cross-validation, and the simpler model is chosen unless the complex one is better by more than one standard error.
- Model choice, any tuning, and thresholds are decided using **5-fold cross-validation within 2007–2014 only**.
- Thresholds: (a) **matched-rate**, referring the same share as the baseline; (b) **high-sensitivity**, ≥ 80 % of cases caught in training.

## 7. Analyses on the 2015–2018 test set
Confidence intervals use a **cluster bootstrap** (5,000 resamples, seed 42) that resamples NHANES primary sampling units within strata and
cycles, because participants within a sampling unit are not independent.

### 7.1 Primary (success criteria)
- **P1 Diabetes:** at the CDC/ADA score's referral rate, the diabetes model catches more undiagnosed diabetes cases than the score.
  **Success:** the 95 % CI of (model − score) excludes 0 in favour of the model.
- **P2 CKD:** at the KDIGO rule's referral rate, the CKD model catches more undiagnosed CKD cases than the rule.
  **Success:** the 95 % CI excludes 0 in favour of the model.
- P1 and P2 are judged separately. A negative result is reported, not hidden.

### 7.2 Secondary
ROC-AUC, PR-AUC, Brier score, calibration (mean predicted vs observed, slope), saved thresholds applied unchanged, the USPSTF-style rule, and
the prediabetes target (§3).

### 7.3 Interconnection
1. **Overlap:** how often undiagnosed diabetes, undiagnosed CKD markers and hypertension (known or measured) occur together, and the
   prevalence of each conditional on the others.
2. **Does diabetes risk help find CKD?** Add the diabetes model's predicted risk as an input to the CKD model (a "classifier chain"). Compare
   ROC-AUC with and without it; the CI of the difference must exclude 0 for a "yes".
3. **One blood draw for both tests:** a combined policy that refers a person for both tests if *either* model flags them, compared with the
   combined guideline policy (CDC/ADA ≥ 5 **or** KDIGO priority group) at the same overall referral rate. Metric: undiagnosed conditions found
   per 100 referrals.

### 7.4 Fairness
Sensitivity and calibration by sex, age group (20–39, 40–59, 60+) and race/ethnicity, with CIs. Descriptive: large gaps are reported as findings.

### 7.5 Survey weights (sensitivity check)
The primary analysis is unweighted. Key results are repeated with NHANES examination weights to estimate US-population values.

## 8. Known limitations (stated in advance)
- A single measurement of HbA1c, creatinine and albumin, while clinical diagnosis needs confirmation (CKD needs 3 months).
- The CDC/ADA test targets prediabetes. Physical activity and smoking are self-reported, and question wording varies slightly between cycles.
- Lab methods for HbA1c and creatinine changed over the years. Any drift between the training and test periods is part of what the temporal validation tests.
- Results apply to the US non-institutionalised population. Validation elsewhere is still needed.

## Change log
| Date | Change | Reason |
|---|---|---|
| 2026-11-12 | Plan written before Part 2 outcomes were examined | — |
| 2026-11-12 | Implementation details, fixed **before** outcomes were examined: (1) in the CDC/ADA score, a missing answer scores 0 points for that item; (2) women who were never pregnant (`RHQ131` = 2) and all men have gestational diabetes = 0, while women with no reproductive-health record (~12 %) or a "borderline" answer stay missing; (3) BP medication = 0 when not told of high BP or not prescribed medication; (4) the CKD target is positive if any available kidney marker is abnormal, and negative only when both were measured and normal | Choices the plan didn't specify |
| 2026-11-12 | **Added sensitivity analysis:** repeat P2 and the kidney ROC-AUC with an eGFR < 60-only target. Decided from the **training-year** audit (60 % of kidney cases are raised albumin only, on a single test). Test-year outcomes not yet examined. | A single albumin test overstates CKD |
| 2026-11-12 | **Bootstrap corrected (§7):** every test-year stratum has exactly 2 PSUs, and the pre-registered "resample PSUs within strata" bootstrap then understates variance by half. Use the Rao–Wu rescaling bootstrap (m = n − 1: draw one PSU per stratum and count it twice), which is unbiased for this design (`src/part2_eval.py`, tested against the textbook variance). Decided from the design structure, before test-year outcomes were examined. | Correct confidence intervals |
| 2026-11-12 | **Implementation of §7.3.3 (combined policy):** each person's combined score is the larger of (diabetes risk ÷ diabetes standard threshold) and (kidney risk ÷ kidney standard threshold). The top-scoring people are referred, up to the same overall rate as the guideline combination. Evaluated in adults belonging to both target populations. | The plan didn't say how to combine two risks |
| 2026-11-12 | **Exploratory addition (§7.3, not a success criterion):** "HbA1c first", i.e. does the *actual* HbA1c result, as new information, improve kidney-marker detection over the kidney model? Fitted on 2007–2014, compared on 2015–2018. Motivated by the training-year finding that *predicted* diabetes risk adds nothing. | Tests where the interconnection can be used |
| 2026-11-12 | **Results recorded (notebook 12). Criteria unchanged.** P1 (diabetes) not met: −0.3 points (−4.2 to +3.6). P2 (kidney) met: +2.5 points (+1.0 to +4.0). | Test years evaluated once with the saved models |
