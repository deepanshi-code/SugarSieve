# SugarSieve: final report

**Question:** Can quick clinic measurements decide who should be sent for an oral glucose tolerance test (OGTT) better than a simple guideline rule?
**Development data:** Pima Indians Diabetes Database (NIDDK, via OpenML #37): 768 women aged 21+.
**External validation data:** US NHANES 2005–2016: 5,298 women aged 21+ without diagnosed diabetes.
**Live app:** [sugarsieve.streamlit.app](https://sugarsieve.streamlit.app/) · **Code and notebooks:** this repository

---

## 1. Summary

- **Main question, mixed result:** using quick measurements only (age, BMI, blood pressure, pregnancies, family history, skinfold),
  a logistic regression **did not beat the guideline rule** *"refer if age ≥ 35 and BMI ≥ 25"* on the small Pima test set: −5.6 points of
  cases caught at the rule's referral rate (95 % CI −14.3 to +6.0). **In a large, independent external validation (NHANES), it did:**
  +6.9 points (95 % CI +3.2 to +10.9). The Pima interval was wide enough to include that effect.
- **The model's ranking ability transferred to a new population:** ROC-AUC 0.730 on Pima and **0.739** on NHANES, without retraining
  and with two inputs unavailable. **Its probabilities did not:** it predicted 33 % average risk where 8.5 % had diabetes. A single
  recalibration step fixed that.
- **Secondary question, met twice:** with lab values, the full model ranks patients better than glucose alone, on Pima (+0.048 ROC-AUC,
  95 % CI +0.004 to +0.095) and on NHANES (+0.027, 95 % CI +0.008 to +0.047). The margin is real but small.
- **The age finding was population-specific.** In Pima, nearly half of all cases were women under 35, whom the age-gated rule can never refer.
  In NHANES only 4 % were, and there the model beat the rule in both age groups.
- **Most missed Pima cases had normal glucose** at the exam (22 of 24), which points to diabetes that developed later.
- **A simple model won.** Logistic regression beat Random Forest and Gradient Boosting. The information available (lab values or not)
  mattered far more than the choice of algorithm.

## 2. Why this question

The OGTT needs a fasting patient, a glucose drink, a two-hour wait and a blood draw. It is too costly to give everyone, so
clinics need a cheap way to decide **who to test**. A model only earns its place in that workflow if it does better than what clinics
already use: a simple age-and-weight rule. So the comparison that matters is **model vs rule at the same referral rate**, not
model accuracy on its own.

The dataset's glucose value comes from the OGTT itself. A model that uses it is partly re-reading the test result.
That is why the project keeps two feature sets apart: **no-lab** (before the test) and **full** (after it).

## 3. Data

768 women of Pima heritage near Phoenix, Arizona, examined in the 1980s. A woman is labelled positive if she showed diabetes by WHO criteria
(2-hour glucose ≥ 200 mg/dL) **at any survey examination or in routine care**. 35 % are positive.

Quality issues found in the audit ([notebook 01](../notebooks/01_data_audit.ipynb)):

| Issue | Evidence | How it was handled |
|---|---|---|
| The documentation says "no missing values", but zeros stand in for missing values | Insulin is 0 in 47 % of training rows and skinfold in 29 %. 48 % of rows have at least one impossible zero. | Zeros converted to missing. Rows are never dropped. |
| Missing values follow a pattern | Whenever skinfold is missing, insulin is missing too | Imputation inside the cross-validation pipeline |
| Leaving zeros in hides real signal | Insulin's single-feature ROC-AUC rises from 0.56 to 0.75 once zeros are treated as missing | The zero → missing step is applied everywhere, including the app |

## 4. Method

**Decided before modelling** ([problem_definition.md](problem_definition.md)): the questions, the baselines and the success criteria.
The change log there shows they were not changed after the results came in.

1. **One fixed split:** 614 training and 154 test patients, stratified, seed 42. The test set was used **once**, in notebook 03.
2. **Model comparison** ([notebook 02](../notebooks/02_modelling.ipynb)): 5-fold × 10-repeat stratified cross-validation on the training set,
   with every model scored on the same 50 splits (a paired comparison). All preprocessing sits inside scikit-learn pipelines, so no
   information leaks from validation folds.
3. **Candidates:** logistic regression (with median or iterative imputation, an optional log transform, optional missing-value indicators),
   Random Forest and Gradient Boosting.
4. **Selection rule:** the simplest model within one standard error of the best. This picked **plain logistic regression with median
   imputation** for both feature sets. Tuning `C` from 0.01 to 10 changed scores by ≤ 0.006.
5. **Calibration:** class weighting was rejected. It left the ranking unchanged (AUC 0.837 vs 0.835) but inflated the predicted risks.
6. **Thresholds** were set on out-of-fold training predictions: a *matched-rate* threshold that refers as many patients as the rule, and a
   *high-sensitivity* threshold that catches at least 80 % of cases in training.
7. **Final test** ([notebook 03](../notebooks/03_test_evaluation.ipynb)): the saved models were evaluated unchanged, with paired bootstrap
   95 % confidence intervals (5,000 resamples).
8. **External validation** ([notebook 05](../notebooks/05_external_validation.ipynb)): the saved models were applied unchanged to NHANES,
   following a plan committed before any outcome was examined ([external_validation_plan.md](external_validation_plan.md)).

**Primary metric:** *sensitivity at the rule's referral rate*. Each model refers the same number of patients as the rule, and we count
how many diabetes cases each one catches. This compares the models fairly at the operating point a clinic actually uses.

## 5. Results (Pima)

### Cross-validation (training data, mean of 50 splits)

| Model | Cases caught at rule's referral rate | ROC-AUC | PR-AUC |
|---|---|---|---|
| Guideline rule (age ≥ 35 & BMI ≥ 25) | 0.509 | 0.638 | 0.449 |
| **No-lab** logistic regression | 0.519 | 0.753 | 0.603 |
| Glucose only | 0.609 | 0.798 | 0.707 |
| **Full** logistic regression | 0.646 | 0.840 | 0.735 |

### Test set (154 patients, 54 with diabetes)

| Model | Cases caught at rule's referral rate | ROC-AUC | PR-AUC | Brier score |
|---|---|---|---|---|
| Guideline rule | 0.519 | 0.659 | 0.471 | – |
| **No-lab** model | 0.463 | 0.730 | 0.553 | 0.200 |
| Glucose only | 0.500 | 0.765 | 0.595 | 0.193 |
| **Full** model | 0.519 | 0.813 | 0.673 | 0.175 |

### Verdicts against the pre-set criteria

| Comparison | Difference (95 % CI) | Criterion met? |
|---|---|---|
| No-lab model − rule (cases caught at rule's rate) | −0.056 (−0.143 to +0.060) | ❌ No |
| Full model − glucose only (ROC-AUC) | +0.048 (+0.004 to +0.095) | ✅ Yes |

### The saved thresholds on the test set

| Model / threshold | Share referred | Cases caught | Missed cases |
|---|---|---|---|
| Guideline rule | 31 % | 52 % | 26 |
| No-lab, standard | 34 % | 52 % | 26 |
| No-lab, catch-more | 55 % | 76 % | 13 |
| Full, standard | 34 % | 56 % | 24 |
| Full, catch-more | 53 % | 87 % | 7 |

The thresholds chosen on training data transferred well: the standard thresholds referred 34 %, against a target of about 33 %.

## 6. What we learned (Pima)

1. **A simple rule is hard to beat with weak features, in a small sample.** None of the no-lab measurements is strong on its own
   (best single-feature AUC ≈ 0.69, BMI). Combining them gives a smoother ranking (AUC 0.75 vs the rule's 0.64), but at the one
   cut-off a clinic actually uses, the rule did just as well on Pima. (Section 7 shows a modest advantage in a much larger sample.)
2. **Information beats algorithms.** Adding glucose and insulin raised cross-validated ROC-AUC from 0.75 to 0.84. No modelling choice on the
   no-lab features gained more than about one point.
3. **Who gets missed matters as much as how many.** In Pima the rule and the models caught similar *numbers* of cases, but *different people*.
   [Notebook 04](../notebooks/04_age_subgroups.ipynb) checks this on all 768 patients, using out-of-fold predictions for the training set:

   | Diabetes cases | Rule catches | No-lab model | Full model |
   |---|---|---|---|
   | Under 35 (126 cases) | 0 % | 34 % (26–43 %) | 52 % (44–61 %) |
   | 35 and over (142 cases) | 96 % (93–99 %) | 65 % (58–73 %) | 73 % (65–80 %) |

   (95 % bootstrap confidence intervals in brackets.)

   Nearly half of Pima's cases are under 35, and the rule can't refer them at all. The models move referrals from older women without
   diabetes to younger women with it. *Caveat:* this is exploratory, and Section 7 shows the pattern depends on the population.
4. **Some cases can't be caught from one visit.** The missed cases had a median 2-hour glucose of 122 mg/dL, against 155 for the cases
   that were caught, and 22 of the 24 were below 140 mg/dL. The label counts diabetes found at any later examination, so many of these women
   were probably diagnosed later. A negative screen is therefore not a clean bill of health.
5. **Probabilities need care.** On average the models were well calibrated on Pima (predicted 0.35 vs actual 0.35), but they
   overestimated risk at the top end. That's why the app shows **risk bands** instead of precise percentages.
6. **The app's explanations are exact for this model.** For a logistic regression, each bar in the app's "What drove this result" chart
   (coefficient × standardised value) equals that feature's exact SHAP value in log-odds for the model's imputed, standardised inputs,
   measured against the average training patient. So no separate explanation library is needed, and the explanation isn't an approximation.

## 7. External validation (NHANES)

**Why:** every result above comes from one community of women in the 1980s. The strongest test of a model is whether it still works
on people it has never seen, from a different place and time.

**Data:** US National Health and Nutrition Examination Survey (CDC/NCHS), 2005–2016. These are **5,298 women aged 21+, not pregnant, not
previously diagnosed with diabetes, and with a completed OGTT**. The outcome is **undiagnosed diabetes by lab criteria**: 2-hour glucose
≥ 200 mg/dL, fasting glucose ≥ 126 mg/dL, or HbA1c ≥ 6.5 %. 451 women (8.5 %) are positive. The family-history score and 2-hour insulin
aren't available, so they are passed as missing, as the app does. Skinfold exists only for 2005–2010.

**Protocol:** the plan, with its success criteria, was written and committed **before** any outcome was examined. The saved models were
used unchanged. Full details are in [notebook 05](../notebooks/05_external_validation.ipynb).

| Pre-set question | Pima test (154 women) | NHANES (5,298 women) |
|---|---|---|
| No-lab model − rule, cases caught at rule's rate | −5.6 points (−14.3 to +6.0) ❌ | **+6.9 points (+3.2 to +10.9) ✅** |
| No-lab model ROC-AUC | 0.730 | **0.739 (0.718–0.760) ✅** |
| Guideline rule ROC-AUC | 0.659 | 0.642 (0.622–0.663) |
| Full model − glucose alone, ROC-AUC* | +0.048 (+0.004 to +0.095) ✅ | **+0.027 (+0.008 to +0.047) ✅** |
| Mean predicted risk vs observed rate (no-lab) | 0.35 vs 0.35 | **0.33 vs 0.085 ❌** |

\*NHANES: restricted to 2-hour glucose < 200 mg/dL with outcome fasting glucose ≥ 126 or HbA1c ≥ 6.5 %, to avoid a circular test.

**What it shows**
1. **Ranking transfers.** The no-lab model's ROC-AUC barely moved (0.730 → 0.739), despite a different era, all ethnicities, an older
   population (median age 47 vs 29), and two missing inputs.
2. **In a large sample, the no-lab model beats the rule.** At the rule's referral rate (52 % of these older women), it caught 85 % of cases
   against the rule's 78 %. This doesn't contradict Pima: the Pima interval (−14 to +6 points) included this effect, but 54 test cases were
   too few to detect it. The comparison also happens at a broader referral rate than in Pima (52 % vs 31 %).
3. **Probabilities don't transfer and must be recalibrated.** The model expected 33 % risk where 8.5 % had diabetes. Updating only the
   intercept (−1.91 log-odds, fitted on half the data) brought the mean prediction to 8.6 % on the other half and **halved the Brier score
   (0.148 → 0.074)**, with ROC-AUC unchanged.
4. **The age trade-off was specific to Pima.** Only 18 of 451 NHANES cases (4 %) were under 35. There the model caught more cases than the
   rule in **both** age groups (35+: 86 % vs 81 %). Pima's early-onset diabetes is what made the rule look strong for older women.
5. **The results don't depend on how missing family history is handled.** Mapping the yes/no question onto the pedigree score changed the
   ROC-AUC from 0.739 to 0.741.
6. **The saved thresholds don't keep their meaning.** In NHANES the standard threshold referred 29 % (not 33 %) and caught 60 % of cases.
   The thresholds need to be re-chosen for each population, along with the recalibration.

**Limitations of this validation:** survey weights weren't used, so the results describe these sampled women, not the US population. The
outcome is current undiagnosed diabetes, while Pima's also included later onset. Women only. And the full model can't be judged fairly with
its saved thresholds here, because glucose ≥ 200 defines part of the outcome.

## 8. Limitations

- **Small development sample.** With 154 Pima test patients and 54 cases, the internal test has wide confidence intervals. One patient
  changes sensitivity by about 2 points. The NHANES validation (451 cases) is far more precise.
- **Development population.** The models were trained on Pima women aged 21+ from the 1980s. NHANES shows the ranking transfers to
  US women, but **men, other countries and today's clinical practice remain untested**.
- **Different labels.** Pima's outcome includes later-onset diabetes, while NHANES uses current undiagnosed diabetes.
- **A simplified baseline.** The rule "age ≥ 35 and BMI ≥ 25" is a simplified form of published screening guidance (based on USPSTF 2021).
  Check the current guideline before relying on this comparison.
- **Heavily studied data.** The Pima dataset is widely used, so similar studies on it aren't independent evidence. The NHANES validation is.

## 9. What real use would require

SugarSieve is a research prototype, **not a medical device**. To support real referral decisions, it would need at least the following:

1. **Validation in the actual target setting.** NHANES was a first external check, on US women. The clinic population where it would be used
   needs its own check, including men if they are in scope.
2. **Recalibration and re-chosen thresholds** for the local diabetes rate. NHANES showed that both are necessary, and that a simple intercept
   update can be enough.
3. **Comparison with the tests used today.** Many settings screen with HbA1c or fasting glucose rather than the OGTT. The real question may
   be "who needs HbA1c", which needs different data.
4. **A prospective study** measuring whether using the tool changes outcomes: cases found, tests saved, time to diagnosis.
5. **A fairness review** across age, sex and ethnicity before any deployment. The age pattern differed sharply between populations.
6. **Regulatory assessment.** Software that influences clinical decisions may count as a medical device, depending on the jurisdiction.
7. **Monitoring after deployment**, for drift in the patient mix and in calibration.

## 10. Reproducing the results

```bash
pip install -r requirements-dev.txt
python -m unittest discover tests      # 16 tests (also run automatically on GitHub)
python -m src.nhanes                   # download NHANES (~116 MB) and rebuild data/external/nhanes_validation.csv
jupyter lab                            # run notebooks 01 → 05 in order
streamlit run app.py
```

All randomness is seeded (split seed 42; cross-validation seed 42; bootstrap seed 42). Notebook 02 re-creates `models/`. Notebooks 03 and 05
are meant to be run once, and re-running them gives identical numbers.

**Data sources:** Pima Indians Diabetes Database (NIDDK; via OpenML #37). National Health and Nutrition Examination Survey (NHANES),
Centers for Disease Control and Prevention, National Center for Health Statistics, 2005–2016 (public domain).
