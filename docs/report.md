# SugarSieve: final report

**Question:** Can quick clinic measurements decide who should be sent for an oral glucose tolerance test (OGTT) better than a simple guideline rule?
**Data:** Pima Indians Diabetes Database (NIDDK, via OpenML #37): 768 women aged 21+.
**Live app:** [sugarsieve.streamlit.app](https://sugarsieve.streamlit.app/) · **Code and notebooks:** this repository

---

## 1. Summary

- **Main question, negative result:** using quick measurements only (age, BMI, blood pressure, pregnancies, family history, skinfold),
  a logistic regression **did not beat the guideline rule** *"refer if age ≥ 35 and BMI ≥ 25"*. At the rule's own referral rate it caught
  **5.6 points fewer** cases on the test set, with a 95 % CI of −14.3 to +6.0 points. In cross-validation it was a tie (+1.0 point).
- **Secondary question, met:** when lab values are available, the full model ranks patients better than glucose alone
  (ROC-AUC **0.813 vs 0.765**, difference +0.048, 95 % CI **+0.004 to +0.095**). The margin is real but may be small.
- **Most useful finding:** **nearly half of all diabetes cases (126 of 268) are women under 35**, and the age-gated rule **cannot refer any of them**.
  The models catch 34 % (quick measurements) to 52 % (with lab results) of these young cases. In exchange, they catch fewer older cases.
  The rule and the models catch similar *numbers* of cases, but *different people* (exploratory analysis, [notebook 04](../notebooks/04_age_subgroups.ipynb)).
- **22 of the 24 cases the full model missed had normal glucose** at the exam, which points to diabetes that developed later.
- A simple model won. Logistic regression beat Random Forest and Gradient Boosting, and the information available (lab values or not)
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

**Primary metric:** *sensitivity at the rule's referral rate*. Each model refers the same number of patients as the rule, and we count
how many diabetes cases each one catches. This compares the models fairly at the operating point a clinic actually uses.

## 5. Results

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

## 6. What we learned

1. **A simple rule is hard to beat with weak features.** None of the no-lab measurements is strong on its own (best single-feature AUC ≈ 0.69, BMI).
   Combining them gives a smoother ranking (AUC 0.75 vs the rule's 0.64), but at the one cut-off a clinic actually uses, the rule did just as well.
   What the model really offers is **choice**: a clinic can set the referral rate to match its testing capacity.
2. **Information beats algorithms.** Adding glucose and insulin raised cross-validated ROC-AUC from 0.75 to 0.84. No modelling choice on the
   no-lab features gained more than about one point.
3. **Who gets missed matters as much as how many.** The rule and the models caught similar *numbers* of cases, but *different people*.
   The test set had only 16 young cases, so [notebook 04](../notebooks/04_age_subgroups.ipynb) repeats the check on all 768 patients,
   using out-of-fold predictions for the training set. It found the same pattern:

   | Diabetes cases | Rule catches | No-lab model | Full model |
   |---|---|---|---|
   | Under 35 (126 cases) | 0 % | 34 % (26–43 %) | 52 % (44–61 %) |
   | 35 and over (142 cases) | 96 % (93–99 %) | 65 % (58–73 %) | 73 % (65–80 %) |

   (95 % bootstrap confidence intervals in brackets.)

   - **Nearly half of all cases here are under 35.** The rule can't refer them at all, because it requires age ≥ 35.
   - The models also refer **fewer older women without diabetes**. Among 30–44-year-olds without diabetes in training, the rule refers 50 %
     and the full model 22 %. So the models **move** referrals from older patients without diabetes to younger patients with diabetes.
   - This changes how the main result reads. The no-lab model didn't catch *more* cases, but it catches a group the rule can't reach.
     Whether that trade-off is better is a clinical and policy decision, not a statistical one.
   - *Caveats:* this analysis is **exploratory** and was added after the main evaluation. The rule's 0 % is true by construction. And this
     population has unusually early-onset diabetes, so in other populations the share of young cases may be much smaller.
4. **Some cases can't be caught from one visit.** The missed cases had a median 2-hour glucose of 122 mg/dL, against 155 for the cases
   that were caught, and 22 of the 24 were below 140 mg/dL. The label counts diabetes found at any later examination, so many of these women
   were probably diagnosed later. A negative screen is therefore not a clean bill of health.
5. **Probabilities need care.** On average the models were well calibrated (predicted 0.35 vs actual 0.35), but they overestimated
   risk at the top end. That's why the app shows **risk bands** instead of precise percentages.
6. **The app's explanations are exact for this model.** For a logistic regression, each bar in the app's "What drove this result" chart
   (coefficient × standardised value) equals that feature's exact SHAP value in log-odds for the model's imputed, standardised inputs, measured against the average training patient. So no
   separate explanation library is needed, and the explanation isn't an approximation.

## 7. Limitations

- **Small sample.** With 154 test patients and 54 cases, every test figure has wide confidence intervals. One patient changes sensitivity by about 2 points.
- **Narrow population.** Pima women aged 21+, examined in the 1980s. This group has a very high diabetes rate, and results may not transfer
  to other ethnicities, to men, or to today's clinical practice.
- **Mixed label.** The outcome combines diabetes found at the examination with diabetes found later, while the features come from a single visit.
- **A simplified baseline.** The rule "age ≥ 35 and BMI ≥ 25" is a simplified form of published screening guidance (based on USPSTF 2021).
  Check the current guideline before relying on this comparison.
- **The same data, studied heavily.** This dataset is widely used. Choices made here were based on the training data only, but similar
  studies on it can't be treated as independent evidence.

## 8. What real use would require

SugarSieve is a research prototype, **not a medical device**. To support real referral decisions, it would need at least the following:

1. **External validation** on current patients from the target population, ideally several sites. That would check discrimination,
   calibration and subgroup performance, especially for younger patients.
2. **Recalibration** to the local diabetes rate. A model trained where 35 % have diabetes will overestimate risk where 10 % do.
3. **Comparison with the tests used today.** Many settings screen with HbA1c or fasting glucose rather than the OGTT. The real question may
   be "who needs HbA1c", which needs different data.
4. **A prospective study** measuring whether using the tool changes outcomes: cases found, tests saved, time to diagnosis.
5. **A fairness review** across age, sex and ethnicity before any deployment, given the age effect found here.
6. **Regulatory assessment.** Software that influences clinical decisions may count as a medical device, depending on the jurisdiction.
7. **Monitoring after deployment**, for drift in the patient mix and in calibration.
8. **A deliberate referral policy for young patients.** Given the age finding, one option to test is a hybrid: *refer if the rule says yes,
   or if the model's risk is high for a patient under 35*. It would need its own pre-set criteria and fresh data to be evaluated fairly.

## 9. Reproducing the results

```bash
pip install -r requirements-dev.txt
python -m unittest discover tests      # 11 tests
jupyter lab                            # run notebooks 01 → 02 → 03 → 04 in order
streamlit run app.py
```

All randomness is seeded (split seed 42; cross-validation seed 42; bootstrap seed 42). Notebook 02 re-creates `models/`. Notebook 03 is
meant to be run once, and re-running it gives identical numbers.
