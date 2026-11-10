# Model card: SugarSieve referral models

A one-page summary of what the two saved models are, what they are for, and how far they can be trusted.
Details are in the [report](report.md).

## Model details
| | No-lab model (`models/no_lab.joblib`) | Full model (`models/full.joblib`) |
|---|---|---|
| Purpose | Suggest who to refer for an oral glucose tolerance test (OGTT) | Flag patients for follow-up once OGTT results exist |
| Inputs | Pregnancies, diastolic blood pressure, triceps skinfold, BMI, diabetes pedigree function, age | The same, plus 2-hour glucose and 2-hour insulin |
| Algorithm | Median imputation → standardisation → logistic regression (`C = 1`, no class weighting) | Same |
| Output | Probability of diabetes, turned into a referral by a fixed threshold | Same |
| Thresholds | Standard 0.422 (refers ~1 in 3); catch-more 0.283 (refers ~1 in 2) | Standard 0.418; catch-more 0.250 |
| Library | scikit-learn 1.8.0, Python 3.13 | Same |
| Portable copy | `models/coefficients.json`: every number needed to compute predictions without scikit-learn (`src/export.py`) | Same |

Coefficients (log-odds per 1 standard deviation): no-lab model: BMI 0.69, age 0.37, pregnancies 0.30, pedigree 0.28, skinfold 0.11,
blood pressure 0.07. Full model: glucose 1.18, BMI 0.69, pregnancies 0.38, pedigree 0.23, age 0.15, skinfold 0.03, blood pressure −0.04, insulin −0.07.

## Intended use
- **Intended:** a teaching and research demonstration of how to build and honestly evaluate a screening-referral model.
- **Not intended:** clinical decisions about real patients. It is not a medical device and has not been clinically validated.
- **Intended users:** students, data scientists and reviewers studying the method, not clinicians or patients.

## Training data
Pima Indians Diabetes Database (NIDDK, via [OpenML #37](https://www.openml.org/d/37)): 768 women aged 21+ of Pima heritage, Arizona, 1980s.
Of these, 614 were used for training and 154 held out for a single final test. Zeros meaning "not measured" were converted to missing values.
The label is diabetes by WHO criteria at the examination or found later.

## Performance (held-out test set, 154 patients)
| | ROC-AUC | Cases caught at the guideline's referral rate | Brier score |
|---|---|---|---|
| Guideline rule (age ≥ 35 & BMI ≥ 25) | 0.659 | 0.519 | – |
| No-lab model | 0.730 | 0.463 | 0.200 |
| Full model | 0.813 | 0.519 | 0.175 |

- The no-lab model **did not beat** the guideline rule: −5.6 points of cases caught (95 % CI −14.3 to +6.0).
- The full model beat glucose alone: ROC-AUC +0.048 (95 % CI +0.004 to +0.095).

## External validation (NHANES 2005–2016, 5,298 US women without diagnosed diabetes)
Applied unchanged, following a [plan written before outcomes were examined](external_validation_plan.md) ([notebook 05](../notebooks/05_external_validation.ipynb)).

| | Result (95 % CI) |
|---|---|
| No-lab model ROC-AUC | 0.739 (0.718–0.760), vs 0.730 on the Pima test |
| No-lab model − guideline rule, cases caught at the rule's referral rate | +6.9 points (+3.2 to +10.9) |
| Full model − glucose alone, ROC-AUC (2-hour glucose < 200 subset) | +0.027 (+0.008 to +0.047) |
| Mean predicted risk vs observed rate | 0.33 vs 0.085 (**overestimates**); after intercept recalibration 0.086 vs 0.085 |

## Known limitations and risks
- **Probabilities must be recalibrated** before use in a new population. Ranking transferred to NHANES, but risks were about 4× too high.
  The **saved thresholds also need re-choosing**, because they don't keep their referral rate in a new population.
- **Untested groups:** men, populations outside the US, and current clinical practice.
- **Age:** in Pima the models caught more cases than the guideline rule in women under 35 but fewer in women 35+
  ([notebook 04](../notebooks/04_age_subgroups.ipynb)). In NHANES they caught more in both groups. Performance by age depends on the population.
- **Later-onset cases:** most missed cases had normal glucose at the visit, so a negative result is not a clean bill of health.
- **Calibration:** good on average, but probabilities above about 60 % ran too high in testing. The app shows risk bands for that reason.
- **Inputs outside the training range** (e.g. 2-hour glucose ≥ 200 mg/dL) are out of scope. The app blocks them.

## Explanations
Each bar in the app's "What drove this result" chart is the coefficient × the standardised input. For a logistic regression this equals the
exact SHAP value in log-odds, relative to the average training patient.

## Ethical considerations
- The data is public and de-identified. The app stores nothing.
- Age is used as a predictor. That improves risk estimates, but it means performance differs by age group, as shown above.
