# Problem definition

*Written before any modelling. Changing these criteria after seeing results is not allowed. If they change, record why below.*

## 1. Problem
Type 2 diabetes is often undiagnosed for years. The test that confirms it, an **oral glucose tolerance test (OGTT)**, needs a fasting
patient, a glucose drink, a 2-hour wait and a blood draw. It is too costly to give everyone, so clinics need a way to decide
**who should be sent for the test**.

## 2. User and decision
- **User:** a primary-care clinic or community screening programme.
- **Decision supported:** *refer this person for an OGTT, or not?*
- **Inputs available at that moment:** quick measurements only (age, BMI, blood pressure, pregnancies, family history, skinfold).
  Lab values like glucose and insulin are **not** available yet, because they come from the test we are deciding about.

## 3. Research questions
1. **No-lab model:** using only quick measurements, can we pick who to test better than a simple guideline rule?
2. **Full model:** if glucose and insulin *are* available, does a model add anything beyond glucose alone?
3. How much predictive value does the lab test add over quick measurements?

## 4. Data
Pima Indians Diabetes Database (NIDDK, via [OpenML #37](https://www.openml.org/d/37)): 768 women aged 21+ of Pima heritage near Phoenix, USA.
`Outcome = 1` means the woman showed signs of diabetes by WHO criteria (2-hour glucose ≥ 200 mg/dL at a survey exam, or found in routine care).

Known issues, found in the data audit (`notebooks/01_data_audit.ipynb`):
- Zeros are used for missing values (e.g. Insulin missing in 374/768 rows), even though the documentation says there are none.
- The population is narrow: one community, women only, data from the 1980s. **Results will not automatically generalise.**

## 5. Baselines (every model must beat these)
| Question | Baseline |
|---|---|
| All | Refer everyone / refer no one |
| No-lab | **Guideline rule:** refer if Age ≥ 35 **and** BMI ≥ 25. This is based on the USPSTF (2021) recommendation to screen adults aged 35–70 with overweight or obesity; check the current guideline before citing it. |
| Full | **Glucose alone** (single-feature ROC-AUC ≈ 0.79 in the audit) |

## 6. Success criteria
Evaluated with **repeated stratified cross-validation** on the training data, then **once** on a held-out test set (20 %), with 95 % bootstrap confidence intervals.

- **Primary metric:** sensitivity (recall for diabetes) at a fixed referral rate, plus ROC-AUC and PR-AUC.
- **No-lab model succeeds if:** at the **same referral rate as the guideline rule**, it catches more diabetes cases (higher sensitivity),
  and the confidence interval of the difference excludes zero.
- **Full model succeeds if:** its ROC-AUC beats glucose alone by a margin whose confidence interval excludes zero.
- **A negative result is a valid result.** If a model does not beat its baseline, that is reported, not hidden.

## 7. Risks and ethics
- **Missed cases:** false negatives delay diagnosis. That's why sensitivity is the primary metric.
- **Generalisation:** a model trained on Pima women in the 1980s may be miscalibrated for other groups. The app must say so.
- **Not a diagnosis:** the tool only suggests a referral. The OGTT, or another clinical test, still makes the diagnosis.
- **Data:** the dataset is public and de-identified. No new personal data is collected or stored by the app.

## 8. Change log
| Date | Change | Reason |
|---|---|---|
| 2026-11-03 | Initial version | — |
| 2026-11-03 | Results recorded (notebook 03). **Criteria unchanged.** Q1 not met, Q2 met. | Test set evaluated once with the saved models |
| 2026-11-03 | Added an exploratory age-subgroup check. It is not a success criterion. | Safety and fairness check for the app |
