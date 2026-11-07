# SugarSieve: who should get a glucose test?

*Screening works like a sieve: it filters out who needs the full test. SugarSieve checks how well quick measurements do that job.*

**🔗 Live app: [sugarsieve.streamlit.app](https://sugarsieve.streamlit.app/)**

📄 **Full report:** [docs/report.md](docs/report.md): method, results with confidence intervals, limitations, and what real use would need.

## The question
Type 2 diabetes is confirmed with an **oral glucose tolerance test (OGTT)**: fasting, a glucose drink, a 2-hour wait and a blood draw.
It is too costly to give everyone. This project asks:

1. Using only **quick measurements** (age, BMI, blood pressure, pregnancies, family history, skinfold), can a model decide
   **who to refer for the test** better than a simple guideline rule?
2. If lab values *are* available, does a model add anything beyond **glucose alone**?

Full problem statement, baselines and success criteria (fixed before modelling): [docs/problem_definition.md](docs/problem_definition.md)

## Data
[Pima Indians Diabetes Database](https://www.openml.org/d/37) (NIDDK): 768 women aged 21+ of Pima heritage, Arizona, USA.

Key findings from the [data audit](notebooks/01_data_audit.ipynb):
- The documentation says there are no missing values, but **zeros are used for missing values**. About **48 %** of rows have at least one impossible zero (e.g. insulin = 0).
- Treating those zeros as missing matters: insulin's predictive signal goes from ROC-AUC ≈ 0.56 to ≈ 0.75.
- The guideline rule (*Age ≥ 35 and BMI ≥ 25*) refers about 1 in 3 patients but catches only about **half** of the diabetes cases.

## Results
Final evaluation on 154 held-out test patients ([notebook 03](notebooks/03_test_evaluation.ipynb)), judged against criteria fixed before modelling:

| Question | Test result (95 % bootstrap CI) | Verdict |
|---|---|---|
| No-lab model vs guideline rule (cases caught at the same referral rate) | −5.6 points (−14.3 to +6.0) | ❌ Not met: no evidence the model beats the rule |
| Full model vs glucose alone (ROC-AUC) | 0.81 vs 0.77: +0.048 (+0.004 to +0.095) | ✅ Met, with a modest margin |
| Value of lab values | ROC-AUC 0.73 → 0.81; at ~53–55 % referral, 13 → 7 missed cases | Helps most when the goal is to miss few cases |

**Key findings**
- **The simple guideline rule is hard to beat** with quick measurements alone. That's a negative result, consistent in cross-validation and on the test set.
- **The age-gated rule never refers women under 35**, so it caught 0 of 16 young cases in the test set; the models caught 4–6 (exploratory, small numbers).
- **22 of 24 cases the full model missed had normal glucose at the exam**, which suggests later-onset diabetes that a single-visit model can't predict.
- Plain **logistic regression** beat Random Forest and Gradient Boosting in cross-validation ([notebook 02](notebooks/02_modelling.ipynb)).

## Roadmap
- [x] **Stage 1:** problem definition, success criteria, data audit
- [x] **Stage 2:** modelling with repeated CV: no-lab vs full models, baselines, selection, calibration, thresholds
- [x] **Stage 3:** final test-set evaluation with confidence intervals, error and subgroup analysis
- [x] **Stage 4:** Streamlit app (referral suggestion, risk band, explanation, limitations) and tests
- [x] Deployed to Streamlit Community Cloud: [sugarsieve.streamlit.app](https://sugarsieve.streamlit.app/)
- [x] **Stage 5:** [final report](docs/report.md): results, limitations, and what real use would need

## Project structure
```
├── docs/problem_definition.md   # problem, user, baselines, success criteria
├── docs/report.md               # final report
├── data/raw/pima_diabetes.csv   # unchanged copy from OpenML
├── src/data.py                  # loading, zero→missing cleaning, fixed train/test split
├── src/models.py                # pipelines, guideline-rule baseline, screening metric
├── src/predict.py               # prediction logic used by the app (testable without the UI)
├── app.py                       # Streamlit app
├── tests/test_predict.py        # unit tests
├── models/                      # saved models + metadata.json (features, thresholds, CV scores)
└── notebooks/
    ├── 01_data_audit.ipynb
    ├── 02_modelling.ipynb
    └── 03_test_evaluation.ipynb
```

## How to run
```bash
python -m venv .venv
.venv\Scripts\activate          # macOS/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt   # app + notebooks (requirements.txt = app only)

streamlit run app.py                  # the app
python -m unittest discover tests     # the tests
jupyter lab                           # the notebooks
python -m src.data                    # optional: re-download the raw data
```

## The app
A referral aid with two modes:
- **Quick measurements only:** should this patient be referred for a glucose tolerance test?
- **Lab results available:** should this patient be flagged for clinical follow-up?

For each patient it shows a referral suggestion, a **risk band** (lower / moderate / higher) instead of a precise percentage,
a chart of which values drove the result, and warnings that come from the evaluation (young patients, missing values,
and the fact that a negative result is not a clean bill of health). You can switch between a *standard* threshold, which refers
about 1 in 3 patients, and a *catch more cases* threshold, which refers about 1 in 2.

### Deploying (Streamlit Community Cloud, free)
1. Push this folder to a **public GitHub repository**.
2. Sign in at [share.streamlit.io](https://share.streamlit.io) with GitHub → **Create app** → pick the repo, branch `main`, file `app.py`.
3. Under **Advanced settings**, choose **Python 3.13**. The saved models were made with scikit-learn 1.8.0, and `requirements.txt` pins it.
4. Deploy. The app gets a public `*.streamlit.app` URL.

## Limitations
The data covers one community of women from the 1980s. Any model built here is a **learning and research exercise, not a medical device**,
and it would need validation on other populations before real use.
