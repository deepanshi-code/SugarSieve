# External validation plan (NHANES)

*Written and committed **before** any NHANES outcome (diabetes status) was looked at. Only variable names and their availability per cycle
were checked. Any change after results are seen must be logged at the bottom with a reason.*

## Goal
Check whether the saved SugarSieve models, trained on Pima women in the 1980s, keep their behaviour in an **independent, modern,
multi-ethnic** population. The models are applied **exactly as saved**: no retraining. Only the separate recalibration analysis (§5.4) fits anything.

## Data
US National Health and Nutrition Examination Survey (NHANES, CDC/NCHS, public domain), cycles **2005–2006 to 2015–2016**. In these cycles,
a fasting subsample had an oral glucose tolerance test (OGTT). Files are downloaded by `src/nhanes.py`.

## Population (all must hold)
1. Female (`RIAGENDR` = 2), as in Pima.
2. Age 21 or over (`RIDAGEYR` ≥ 21), as in Pima.
3. Not pregnant at the exam (`RIDEXPRG` ≠ 1).
4. **Not previously diagnosed** with diabetes (`DIQ010` ≠ 1). This is a screening population: people who don't know their status.
5. **Has a completed OGTT** (`LBXGLT` present), so the outcome can be determined.

## Outcome: undiagnosed diabetes by lab criteria
Positive if **any** of: 2-hour OGTT glucose ≥ 200 mg/dL; fasting glucose ≥ 126 mg/dL (`LBXGLU`); HbA1c ≥ 6.5 % (`LBXGH`).
*This differs from Pima's label, which also counted diabetes found later. The NHANES label is current diabetes only.*

## Features (mapping to the model's inputs)
| Model input | NHANES source | Notes |
|---|---|---|
| Age | `RIDAGEYR` | Top-coded at 80 or 85 depending on the cycle |
| BMI | `BMXBMI` | |
| BloodPressure | Mean of available `BPXDI1–3` | Readings of 0 treated as missing |
| Pregnancies | `RHQ160`; set to 0 if `RHQ131` = 2 (never pregnant) | Values outside 0–17 (the Pima range) are clipped to 17 |
| SkinThickness | `BMXTRI` | Only 2005–2010; missing in other cycles → filled in by the model |
| DiabetesPedigree | **Not available** (only a yes/no family-history question, `MCQ300C`) | **Primary: missing** → filled in by the model. Sensitivity check: see §5.5 |
| Glucose | `LBXGLT` (2-hour OGTT glucose) | Full model only |
| Insulin | **Not available** (only fasting insulin, which is a different quantity) | Missing → filled in by the model |

Missing values are passed to the saved pipelines as `NaN`, exactly as in the app.

## Analyses
### 5.1 Primary: no-lab model vs guideline rule (same question as the original study)
At the **guideline rule's referral rate in NHANES**, compare the share of diabetes cases caught by the no-lab model and by the rule.
**Success criterion:** the paired bootstrap 95 % CI of (model − rule) excludes 0 in favour of the model. 5,000 resamples, seed 42.

### 5.2 Discrimination
ROC-AUC (with bootstrap CI) for the no-lab model and the rule. For reference, the no-lab model scored 0.730 on the Pima test set.
**Transport criterion:** the no-lab model's ROC-AUC CI lower bound is above 0.60, i.e. it still clearly ranks better than chance.

### 5.3 Saved thresholds
Apply the saved *standard* and *catch-more* thresholds unchanged, and report the referral rate, sensitivity and PPV.
This shows what would happen if the app were used in this population as it is.

### 5.4 Calibration and recalibration
- Calibration-in-the-large (mean predicted risk vs observed rate) and calibration slope.
- **Recalibration demo:** split NHANES 50/50 (stratified, seed 42). Refit only the intercept, or the intercept and slope, on the model's
  log-odds using one half. Evaluate calibration on the other half. Discrimination can't change with this kind of recalibration; only calibration can.

### 5.5 Sensitivity check: family history
Map `MCQ300C` yes → Pima training 75th percentile of DiabetesPedigree, no → 25th percentile, and rerun §5.1–5.2.
This mapping is invented, so it is a **sensitivity check only**.

### 5.6 Age subgroups (replicating notebook 04)
Sensitivity for women under 35 and 35+, for the rule and the no-lab model at the rule's overall referral rate, with bootstrap CIs.

### 5.7 Secondary: full model vs glucose alone
Restricted to women with 2-hour glucose < 200 mg/dL, because otherwise glucose defines the label (circular) and Pima's model range stopped at 199.
Outcome in this analysis: fasting glucose ≥ 126 **or** HbA1c ≥ 6.5 %.
Compare ROC-AUC of the full model vs glucose alone, using a paired bootstrap CI. Glucose alone is used as a raw score.

## Not done (and why)
- **Survey weights:** results describe the sampled women, not the US population. Weighted estimates would be needed for population-level claims.
- **Retraining on NHANES:** the point is to test the *existing* models.
- **Ethnicity subgroups:** possible, but not pre-specified here, and too many unplanned comparisons would weaken the result.

## Change log
| Date | Change | Reason |
|---|---|---|
| 2026-11-09 | Plan written before outcomes were examined | — |
