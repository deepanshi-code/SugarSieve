# SugarSieve Part 2: one visit, three connected conditions (final report)

**Question:** after one routine clinic visit, **which blood tests does this person need**: an HbA1c test for undiagnosed diabetes,
a kidney panel for undiagnosed chronic kidney disease (CKD), both, or neither?
**Data:** NHANES (CDC/NCHS), US adults aged 20+: **22,426** from 2007–2014 (training) and **10,614** from 2015–2018 (test, used once).
**Plan:** [part2_plan.md](part2_plan.md), committed before any outcome was examined, with every later change logged.
**Live app:** [sugarsieve.streamlit.app](https://sugarsieve.streamlit.app/), page "Which blood tests?"

---

## 1. Summary

| Pre-registered question (2015–2018) | Result (95 % CI) | Verdict |
|---|---|---|
| **Diabetes:** does a model catch more undiagnosed diabetes than the official **CDC/ADA risk questionnaire**, at the same referral rate? | −0.3 points (−4.2 to +3.6) | ❌ No: the questionnaire is as good |
| **Kidney:** does a model catch more undiagnosed CKD markers than the **KDIGO 2024 priority groups**, at the same referral rate? | **+2.5 points (+1.0 to +4.0)** | ✅ Yes |
| Does predicted diabetes risk help the kidney model? | +0.0002 ROC-AUC (−0.0012 to +0.0015) | ❌ No |
| One blood draw for both tests: model policy vs guideline policy | +1.4 points of conditions found (0.0 to +2.9) | ➖ Borderline |

**Key findings**
1. **For diabetes, use the free, seven-question CDC/ADA score.** A model using the same routine inputs did not do better. That's a useful
   negative result, and it shows how strong the official tool is. (Part 1's simpler age-and-BMI rule, by contrast, was beaten by 18 points.)
2. **For kidney disease, a model does better than the guideline groups.** It catches 82.5 % vs 80.0 % of cases at the same testing rate, and
   ranks people far better (ROC-AUC 0.788 vs 0.683). The gain grows to +4.7 points when only reduced kidney function (eGFR < 60) counts.
3. **The conditions are strongly connected,** but only *new* information can use that. Undiagnosed diabetes more than doubles the rate of kidney
   markers (29 % vs 13 %), and hypertension triples it. Yet a *predicted* diabetes risk adds nothing to the kidney model, because it comes
   from the same inputs. An *actual* HbA1c result does help (+0.016 ROC-AUC; exploratory).
4. **Fairness:** the diabetes model, which has no race input, **underestimates risk for Asian American adults by more than half**
   (2.1 % predicted vs 5.1 % observed) and catches fewer of their cases than the CDC/ADA score (61 % vs 72 %). The score uses a lower BMI cut-off
   for Asian Americans. **Leaving race out didn't make the model fair.**
5. **Calibration held up over time:** predicted 4.3 % vs 4.0 % observed (diabetes), and 18.1 % vs 17.0 % (kidney), from 2007–2014 to 2015–2018.

## 2. Why this question
Diabetes, high blood pressure and CKD share causes and are often undiagnosed. Diabetes and hypertension are the leading causes of CKD.
Blood pressure is measured at the visit itself, but diabetes needs a blood test (HbA1c) and CKD needs blood and urine tests (creatinine and
albumin). So the practical question is **which tests to order**. A model is only worth using if it does better than the tools clinics already
have: the **CDC/ADA risk test** for diabetes, and the **KDIGO 2024 priority groups** for CKD (*"hypertension, diabetes, and CVD"*).

Blood pressure is not a prediction target, because it is measured at the visit and predicting it would be circular. It links the other two
conditions as an input, and the analysis studies how all three overlap.

Part 2 also fixes the main weaknesses of Part 1: inputs clinics don't collect (skinfold, pedigree score) → routine inputs; the outdated
OGTT → HbA1c; a homemade baseline → official tools; women from the 1980s → men and women from 2007–2018; no check over time → a temporal test.

## 3. Data and definitions
- **Population:** adults aged 20+, examined, not pregnant. **Undiagnosed diabetes:** never told they have diabetes, and HbA1c ≥ 6.5 %.
  **Undiagnosed CKD markers:** never told they have kidney disease, and eGFR < 60 (2021 CKD-EPI, no race term) **or** urine albumin-to-creatinine
  ratio ≥ 30 mg/g (KDIGO 2024 categories).
- **Inputs (no blood tests):** age, sex, BMI, waist, measured blood pressure, known high blood pressure and its treatment, family history of
  diabetes, gestational diabetes, smoking, physical activity, heart disease or stroke, and, for the kidney model, diagnosed diabetes.
  **Race/ethnicity is not an input.** It is used only to check fairness.
- **Verified from source documents:** the CKD-EPI 2021 equation (National Kidney Foundation page), the CKD definition and priority groups
  (KDIGO 2024 guideline PDF, p. S170), and the CDC/ADA scoring (cdc.gov "How Your Test is Scored").
- **Audit** ([notebook 10](../notebooks/10_part2_data_audit.ipynb), training years): undiagnosed diabetes is 3.7 % (2.5 % weighted to the US
  population), and undiagnosed CKD markers are 16.9 % (13.0 % weighted). 60 % of kidney cases are a raised albumin result only, from a single
  urine test. That led to a pre-registered eGFR-only sensitivity check.

## 4. Method
1. **Training:** 2007–2014 only. 5-fold × 3-repeat cross-validation, with each NHANES sampling cluster kept within one fold.
2. **Candidates:** logistic regression and gradient boosting, for each target. The simplest model within one standard error of the best is
   chosen: **logistic regression for diabetes, gradient boosting for kidney** ([notebook 11](../notebooks/11_part2_modelling.ipynb)).
3. **Chain:** the kidney model with predicted diabetes risk as an extra input. It is built without leakage, which a test checks by flipping a
   person's own label and confirming their predicted risk doesn't change.
4. **Thresholds:** chosen on out-of-fold training predictions to refer the same share of people as each official tool.
5. **Test:** one evaluation on 2015–2018 ([notebook 12](../notebooks/12_part2_test_evaluation.ipynb)). Confidence intervals come from a
   **survey-design bootstrap** (Rao–Wu: one sampling unit per stratum, counted twice). The originally planned bootstrap would have understated
   uncertainty, because each stratum has only 2 units. This was corrected, tested against the textbook variance, and committed before the test
   years were examined.

## 5. Results (2015–2018)

| | Diabetes | Kidney |
|---|---|---|
| Adults / cases | 8,523 / 343 (4.0 %) | 9,525 / 1,624 (17.0 %) |
| Official tool refers | 42.9 % (CDC/ADA ≥ 5) | 49.6 % (KDIGO groups) |
| Cases caught: official tool → model, at that rate | 81.6 % → 81.3 % | 80.0 % → **82.5 %** |
| ROC-AUC: official tool → model | 0.751 → 0.763 | 0.683 → **0.788** |
| Mean predicted vs observed | 4.3 % vs 4.0 % | 18.1 % vs 17.0 % |

**Other comparisons:** against Part 1's age-and-BMI rule, the diabetes model catches **+18.1 points** more cases (+10.3 to +25.7). For
prediabetes or diabetes (HbA1c ≥ 5.7 %), the CDC/ADA score is as good (−1.0 points, −2.1 to +0.1). For **eGFR < 60 only**, the kidney model's
advantage grows to **+4.7 points (+2.5 to +6.9)**. With survey weights the conclusions are the same.

**Fairness** (same thresholds for everyone):

| Group | Diabetes: model / CDC-ADA catches | Kidney: model / KDIGO catches |
|---|---|---|
| Age 20–39 | **64 % / 33 %** | 27 % / 32 % |
| Age 60+ | 91 % / **97 %** | **98 % / 90 %** |
| Non-Hispanic Asian | **61 % / 72 %** (model predicts 2.1 % vs 5.1 % observed) | 72 % / 70 % |
| Women | 85 % / 83 % | **80 % / 76 %** |

The CDC/ADA score gives no age points under 40, so it misses most young adults with diabetes, which the model catches more often.

## 6. What the app does with these results
The "Which blood tests?" page ([app_pages/part2.py](../app_pages/part2.py)) turns the evidence into decisions:
- **HbA1c:** decided by the **CDC/ADA score**, because the model was not better. The score's points are shown item by item. The model's risk is
  shown for information only, with a warning for Asian American adults.
- **Kidney panel:** decided by the **kidney model**, because it beat the KDIGO groups. People with diagnosed diabetes are always referred, because
  ADA and KDIGO recommend yearly kidney screening for them.
- **Blood pressure:** a reading at or above 140/90 without known hypertension is flagged for repeat measurement.
- **Connection:** if blood is drawn for HbA1c, the app advises using the result for the kidney decision too.

## 7. Limitations
- **Single measurements.** A clinical diagnosis needs confirmation; for CKD, abnormalities must last at least 3 months. The kidney target
  therefore overstates true CKD, which the eGFR-only check addresses.
- **US data only.** No validation outside NHANES. The CDC/ADA test was designed for prediabetes.
- **Fairness.** The diabetes model's miscalibration for Asian American adults would need fixing before any use (e.g. ethnicity-specific
  recalibration, or ethnicity-aware BMI and waist cut-offs). Small groups have unreliable confidence intervals.
- **Exploratory analyses.** "HbA1c first" and the subgroup tables were not success criteria.
- **Self-reported inputs.** Family history, activity, smoking and history of heart disease are self-reported, and question wording varies
  slightly between survey cycles.

## 8. What would come next
1. Fix the diabetes model's ethnicity miscalibration and test whether it then beats the CDC/ADA score. Or accept the score: it is free and transparent.
2. Formally evaluate an "HbA1c first, then kidney" referral sequence as a pre-registered study on new data.
3. Validate outside the US, and with repeated measurements, to confirm CKD.

## 9. Reproducing
```bash
pip install -r requirements-dev.txt
python -m src.part2_data            # download NHANES 2007–2018 raw files and rebuild the dataset
python -m unittest discover tests   # all tests (also run on GitHub for every push)
jupyter lab                         # notebooks 10 → 11 → 12
```
All randomness is seeded. Notebook 11 recreates `models/part2/`, and notebook 12 is meant to be run once; rerunning it gives identical numbers.

**Sources:** NHANES 2007–2018 (CDC/NCHS, public domain). National Kidney Foundation, *CKD-EPI Creatinine Equation (2021)*. KDIGO 2024 Clinical
Practice Guideline for the Evaluation and Management of CKD, *Kidney International* 105(4S). CDC, *Prediabetes Risk Test: How Your Test is Scored*.
