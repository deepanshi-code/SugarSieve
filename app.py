"""SugarSieve app entry point.  Run with:  streamlit run app.py"""
import streamlit as st

st.set_page_config(page_title="SugarSieve", page_icon="🩺", layout="centered")

# Navigation at the top (not the sidebar), so it stays visible on phones
page = st.navigation([
    st.Page("app_pages/part2.py", title="Which blood tests?", icon="🧪", default=True),
    st.Page("app_pages/part1.py", title="Glucose test referral (Part 1)", icon="🩺"),
], position="top")
page.run()
