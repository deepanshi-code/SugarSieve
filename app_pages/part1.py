"""Part 1 page: referral aid for an oral glucose tolerance test (Pima study). Run the whole app with: streamlit run app.py"""
import altair as alt
import pandas as pd
import streamlit as st

from src.predict import MODES, OPERATING_POINTS, assess, input_ranges

LABELS = {
    "Pregnancies": "Pregnancies",
    "BloodPressure": "Blood pressure",
    "SkinThickness": "Skinfold",
    "BMI": "BMI",
    "DiabetesPedigree": "Family history",
    "Age": "Age",
    "Glucose": "2-hour glucose",
    "Insulin": "2-hour insulin",
}
BAND_ICON = {"Lower": "🟢", "Moderate": "🟡", "Higher": "🔴"}
DECIMALS = {"BMI": 1, "DiabetesPedigree": 2}

ranges = input_ranges()


def number(col, label, step, fmt, help_text, default=None):
    lo, median, hi = ranges[col]
    value = median if default is None else default
    if fmt == "%d":
        return st.number_input(label, int(lo), int(hi), int(value), int(step), help=help_text)
    return st.number_input(label, float(lo), float(hi), float(value), float(step), format=fmt, help=help_text)


def optional_number(col, label, step, fmt, help_text, measured_by_default):
    measured = st.checkbox(f"{label} was measured", value=measured_by_default, key=f"has_{col}")
    if not measured:
        st.caption(f"{label}: not measured. A typical value from the training data is used instead.")
        return None
    return number(col, label, step, fmt, help_text)


st.title("🩺 Glucose test referral (Part 1)")
st.caption("The original Part 1 study, trained on Pima women. For the newer, broader version, open **Which blood tests?** at the top.")
st.write("Should this patient be referred for an **oral glucose tolerance test**? Enter quick measurements to get a "
         "referral suggestion with the reasons behind it. If test results are already available, switch to "
         "*Lab results available* to check whether the patient should be flagged for follow-up.")
st.warning("**Decision support only, not a diagnosis.** The model was built on a single, specific population and "
           "has not been validated elsewhere. Always use clinical judgement.", icon="⚠️")

tab_assess, tab_about = st.tabs(["Assessment", "About & evidence"])

# ---------------------------------------------------------------- assessment
with tab_assess:
    # Settings sit on the page, not in the sidebar, because the sidebar is hidden by default on phones
    s1, s2 = st.columns(2)
    mode = s1.radio("What information do you have?", list(MODES), format_func=MODES.get,
                    help="Quick measurements can be taken in minutes. Lab results come from a 2-hour oral glucose tolerance test.")
    operating_point = s2.radio("Referral threshold", list(OPERATING_POINTS), format_func=OPERATING_POINTS.get,
                               help="'Catch more cases' sends more people for testing, so fewer cases are missed "
                                    "but more tests come back negative.")

    # No st.form: the "was measured" checkboxes must show/hide their inputs immediately,
    # and the result updates live as values change.
    with st.container(border=True):
        st.subheader("Quick measurements")
        c1, c2 = st.columns(2)
        with c1:
            age = number("Age", "Age (years)", 1, "%d", "Training data covers ages 21–81.", default=35)
            bmi = number("BMI", "BMI (kg/m²)", 0.1, "%.1f", "Weight in kg divided by height in m squared.", default=30.0)
            pregnancies = number("Pregnancies", "Number of pregnancies", 1, "%d", "Total number of past pregnancies.")
        with c2:
            pedigree = number("DiabetesPedigree", "Family history score", 0.01, "%.2f",
                              "Diabetes Pedigree Function: higher means more relatives with diabetes, weighted by how closely "
                              "related they are. Leave the typical value (≈0.38) if unknown.")
            bp = optional_number("BloodPressure", "Diastolic blood pressure (mm Hg)", 1, "%d", "The lower blood-pressure number.", True)
            skin = optional_number("SkinThickness", "Triceps skinfold (mm)", 1, "%d", "Needs skinfold calipers.", False)

        glucose = insulin = None
        if mode == "full":
            st.subheader("Lab results (2-hour oral glucose tolerance test)")
            c3, c4 = st.columns(2)
            with c3:
                glucose = number("Glucose", "2-hour plasma glucose (mg/dL)", 1, "%d",
                                 "Model range: 56–199 mg/dL. A value of 200 or more already meets the diagnostic threshold.")
            with c4:
                insulin = optional_number("Insulin", "2-hour serum insulin (µU/mL)", 1, "%d", "Often not measured.", False)
            st.caption("A 2-hour glucose of **200 mg/dL or more** already meets the WHO diagnostic threshold. "
                       "Refer for clinical diagnosis directly; this tool doesn't cover that range.")

    with st.container():
        values = {"Age": age, "BMI": bmi, "Pregnancies": pregnancies, "DiabetesPedigree": pedigree,
                  "BloodPressure": bp, "SkinThickness": skin, "Glucose": glucose, "Insulin": insulin}
        result = assess(values, mode, operating_point)
        icon = BAND_ICON[result["band"]]

        st.subheader("Result")
        # With quick measurements the decision is whether to order the glucose test.
        # With lab results the test is already done, so the decision is whether to flag for clinical follow-up.
        if mode == "no_lab":
            positive, negative = ("**Suggest referral** for an oral glucose tolerance test.",
                                  "**No referral suggested** at this threshold.")
        else:
            positive, negative = ("**Flag for clinical follow-up**: higher diabetes risk given these results.",
                                  "**No follow-up flag** at this threshold.")
        if result["refer"]:
            st.error(positive, icon="📋")
        else:
            st.success(negative, icon="✅")

        m1, m2 = st.columns(2)
        m1.metric("Risk band", f"{icon} {result['band']}")
        m2.metric("Model estimate", f"≈ {result['probability']:.0%}",
                  help="Approximate. In testing, estimates above ~60 % tended to be too high, so read the band, not the exact number.")

        # The guideline rule decides who gets the test, so it is only a fair comparison before the test
        if mode == "no_lab" and result["guideline_refers"] is not None:
            rule_text = "would refer" if result["guideline_refers"] else "would not refer"
            agree = "agrees" if result["guideline_refers"] == result["refer"] else "**disagrees**"
            st.write(f"The simple guideline rule (*age ≥ 35 and BMI ≥ 25*) {rule_text} this patient, so the model {agree}.")

        st.markdown("##### What drove this result")
        contrib = result["contributions"].rename(index=LABELS).reset_index()
        contrib.columns = ["factor", "effect"]
        contrib["direction"] = contrib["effect"].map(lambda e: "raises risk" if e > 0 else "lowers risk")
        # Okabe-Ito orange/blue: distinguishable with red-green colour blindness (unlike red/green)
        chart = (alt.Chart(contrib)
                 .mark_bar()
                 .encode(x=alt.X("effect:Q", title="Effect compared with an average patient (log-odds)"),
                         y=alt.Y("factor:N", sort="-x", title=None),
                         color=alt.Color("direction:N", scale=alt.Scale(domain=["raises risk", "lowers risk"],
                                                                         range=["#D55E00", "#0072B2"]), title=None),
                         tooltip=["factor", alt.Tooltip("effect:Q", format=".2f")])
                 .properties(height=36 * len(contrib)))
        st.altair_chart(chart, width="stretch")
        avg = result["reference"]
        avg_text = ", ".join(f"{LABELS[c]} {avg[c]:.{DECIMALS.get(c, 0)}f}" for c in avg)
        st.caption(f"Bars compare this patient with the **average patient in the training data** ({avg_text}). "
                   "For example, a BMI of 30 can show as *lowering* risk because the average BMI in this population was higher. "
                   "These are associations, not causes.")

        notes = []
        if result["missing"]:
            names = ", ".join(LABELS[c] for c in result["missing"])
            notes.append(f"**Not measured:** {names}. A typical value was used, so the result is less certain.")
        if age < 35 and not result["refer"]:
            notes.append("**Younger patient:** the guideline rule never refers anyone under 35, and in testing these models "
                         "caught only about a third (quick measurements) to a half (with lab results) of diabetes cases in women "
                         "under 35. Don't rely on a low result alone; consider other risk factors.")
        if not result["refer"]:
            notes.append("**A negative result is not a clean bill of health.** Most cases the models missed had normal "
                         "glucose at the time and were probably diagnosed later. Repeat screening still matters.")
        for note in notes:
            st.info(note)

# ---------------------------------------------------------------- about
with tab_about:
    st.subheader("What this tool is")
    st.write("A research prototype that answers one question: **who should be sent for a glucose tolerance test?** "
             "It uses a logistic regression trained on the Pima Indians Diabetes dataset (NIDDK; 768 women aged 21+, "
             "Arizona, 1980s), with 154 patients held out for a single final test.")

    st.subheader("How well it works (held-out test set)")
    st.table(pd.DataFrame({
        "Question": ["Quick measurements vs guideline rule", "Lab model vs glucose alone"],
        "Result (95 % CI)": ["−5.6 points of cases caught (−14.3 to +6.0)", "ROC-AUC +0.048 (+0.004 to +0.095)"],
        "Verdict": ["Not better than the rule", "Better, modest margin"],
    }).set_index("Question"))
    st.markdown(
        "- **Quick measurements alone don't beat the simple guideline rule.** What the model adds is a choice of threshold, "
        "not higher accuracy.\n"
        "- **Nearly half of all diabetes cases in this data (126 of 268) are in women under 35**, whom the guideline rule can never "
        "refer. The models catch 34–52 % of them, but fewer older cases than the rule. They catch *different* people, not more people.\n"
        "- **Lab results help most when the goal is to miss few cases:** at a similar referral rate, 7 vs 13 missed cases.")

    st.subheader("Limitations")
    st.markdown(
        "- One population (Pima women, 1980s). Results may not transfer to other people.\n"
        "- A small test set (154 patients, 54 cases), so all numbers carry wide uncertainty.\n"
        "- The label includes diabetes found at later exams, which no single-visit model can fully predict.\n"
        "- No data is stored. Inputs exist only for the duration of your session.")
    st.caption("Research prototype trained on 614 Pima women (21+) from the 1980s. Not a medical device. "
               "Full analysis, code and notebooks are in the project repository.")
