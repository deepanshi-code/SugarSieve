"""Part 2 page: after one routine visit, which blood tests does this person need?"""
import pandas as pd
import streamlit as st

from src.part2_predict import assess_part2

YES_NO = {"No": 0, "Yes": 1, "Don't know": None}


def yes_no(label, help_text=None, default="No", key=None):
    return YES_NO[st.selectbox(label, list(YES_NO), index=list(YES_NO).index(default), help=help_text, key=key)]


st.title("🧪 SugarSieve: which blood tests?")
st.caption("After one routine visit: who needs an HbA1c test for diabetes, and who needs a kidney panel?")
st.warning("**Decision support only, not a diagnosis.** Built and tested on US adults (NHANES 2007–2018). "
           "Always use clinical judgement.", icon="⚠️")

# ---------------------------------------------------------------- inputs
with st.container(border=True):
    st.subheader("About the person")
    c1, c2 = st.columns(2)
    with c1:
        age = st.number_input("Age (years)", 20, 85, 50, help="The models were built on adults aged 20+.")
        male = 1 if st.radio("Sex", ["Woman", "Man"], horizontal=True) == "Man" else 0
        bmi = st.number_input("BMI (kg/m²)", 14.0, 70.0, 28.0, 0.1, format="%.1f")
        waist = st.number_input("Waist (cm)", 55.0, 180.0, 98.0, 0.5, format="%.1f",
                                help="Measured at the visit. In the data, waist predicted diabetes better than BMI.") \
            if st.checkbox("Waist was measured", value=True) else None
        asian = st.checkbox("Asian American", help="The CDC/ADA score uses a lower BMI cut-off (23) for Asian Americans.")
    with c2:
        if st.checkbox("Blood pressure was measured", value=True):
            sbp = st.number_input("Systolic BP (mm Hg, average of readings)", 70, 250, 125)
            dbp = st.number_input("Diastolic BP (mm Hg, average of readings)", 30, 150, 75)
        else:
            sbp = dbp = None
        told_bp = yes_no("Ever told they have high blood pressure?")
        meds = yes_no("Taking blood-pressure medicine?") if told_bp == 1 else 0

    c3, c4 = st.columns(2)
    with c3:
        family = yes_no("Parent, brother or sister with diabetes?")
        gdm = yes_no("Ever had diabetes during pregnancy?") if male == 0 else 0
        diagnosed = yes_no("Already diagnosed with diabetes?")
    with c4:
        smoker = yes_no("Currently smokes?")
        active = yes_no("Physically active?", "Any moderate or vigorous activity at work or leisure, or walking/cycling to get around.",
                        default="Yes")
        cvd = yes_no("Heart disease, heart failure or stroke?")

values = {"Age": age, "Male": male, "BMI": bmi, "Waist": waist, "SBP": sbp, "DBP": dbp, "ToldHighBP": told_bp,
          "BPMeds": meds, "FamilyHistoryDiabetes": family, "GestationalDiabetes": gdm, "CurrentSmoker": smoker,
          "PhysicallyActive": active, "CVD": cvd, "DiagnosedDiabetes": diagnosed if diagnosed is not None else 0,
          "Asian": asian}
r = assess_part2(values)

# ---------------------------------------------------------------- results
st.subheader("Suggested tests")
col_a, col_k = st.columns(2)

with col_a:
    st.markdown("##### 🩸 HbA1c (diabetes)")
    h = r["hba1c"]
    if r["diagnosed_diabetes"]:
        st.info("Already diagnosed: HbA1c monitoring is part of routine diabetes care.")
    elif h["refer"]:
        st.error(f"**Suggest an HbA1c test.** CDC/ADA risk score **{h['score']}** (5 or more = high risk).", icon="📋")
    else:
        st.success(f"**No HbA1c test suggested.** CDC/ADA risk score **{h['score']}** (below 5).", icon="✅")
    with st.expander("How the score was calculated"):
        st.table(pd.Series(h["points"], name="points").to_frame())
        st.caption("Official CDC/ADA Prediabetes Risk Test scoring (cdc.gov). It decides here because, in testing on "
                   "2015–2018, a model on the same inputs was not better at finding undiagnosed diabetes.")
    if not r["diagnosed_diabetes"]:
        st.caption(f"Model estimate, for information only: about {h['model_risk']:.0%} chance of undiagnosed diabetes.")
        if h["asian_warning"]:
            st.warning("For Asian American adults the model underestimated risk by more than half in testing. "
                       "Rely on the CDC/ADA score, which uses a lower BMI cut-off.", icon="⚠️")

with col_k:
    st.markdown("##### 🫘 Kidney panel (creatinine + urine albumin)")
    k = r["kidney"]
    if k["refer"]:
        reason = ("yearly kidney screening is recommended for everyone with diabetes (ADA and KDIGO)"
                  if k["because_diagnosed_diabetes"] else f"estimated risk {k['risk']:.0%} is above the referral threshold")
        st.error(f"**Suggest a kidney panel**: {reason}.", icon="📋")
    else:
        st.success(f"**No kidney panel suggested.** Estimated risk {k['risk']:.0%} is below the referral threshold.", icon="✅")
    st.caption(f"Estimated chance of undiagnosed kidney-disease markers: **{k['risk']:.0%}**. "
               f"KDIGO priority group (high BP, diabetes or heart disease): **{'yes' if k['kdigo_priority'] else 'no'}**. "
               "In testing, this model found more cases than the KDIGO groups at the same testing rate.")

b = r["blood_pressure"]
if b["new_finding"]:
    st.warning(f"**Blood pressure {b['sbp']:.0f}/{b['dbp']:.0f} mm Hg** is at or above 140/90, with no known high blood "
               "pressure. Confirm with repeat readings. In the data, high blood pressure went with about three times the rate of "
               "undiagnosed diabetes and of kidney-disease markers.",
               icon="🩺")
elif b["measured_high"]:
    st.info("Blood pressure is at or above 140/90 at this visit, in someone with known high blood pressure.", icon="🩺")

if r["hba1c"]["refer"] or r["diagnosed_diabetes"]:
    st.info("**If blood is drawn for HbA1c, use the result for the kidney decision too.** In testing, an actual HbA1c "
            "result improved kidney-disease detection, while a *predicted* diabetes risk did not.", icon="🔗")
st.info("**A negative result is not a clean bill of health.** Both tools miss some cases (about 1 in 5), especially in "
        "adults under 40. Single test results also need confirming before a diagnosis.", icon="ℹ️")

# ---------------------------------------------------------------- evidence
with st.expander("About & evidence"):
    st.markdown(
        "Trained on US adults from NHANES 2007–2014 and tested once on 2015–2018, against criteria written before the results "
        "were seen.")
    st.table(pd.DataFrame({
        "Question": ["Diabetes: model vs CDC/ADA score", "Kidney: model vs KDIGO priority groups"],
        "Result (95 % CI)": ["−0.3 points of cases caught (−4.2 to +3.6)", "+2.5 points (+1.0 to +4.0)"],
        "So this app uses": ["the CDC/ADA score", "the kidney model"],
    }).set_index("Question"))
    st.markdown(
        "- **Connected conditions:** undiagnosed diabetes more than doubled the rate of kidney-disease markers (29 % vs 13 %), "
        "and high blood pressure tripled it.\n"
        "- **Fairness:** the diabetes model underestimated risk for Asian American adults, one reason the official score is used.\n"
        "- **Limits:** US data only; single test results; no data is stored by this app.")

# On phones the top navigation folds into a menu, so link Part 1 on the page too
st.page_link("app_pages/part1.py", label="Part 1: the original glucose-test referral study (Pima)", icon="🩺")
