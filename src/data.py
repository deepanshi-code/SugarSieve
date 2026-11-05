"""Loading and cleaning the Pima Indians Diabetes dataset.

Shared by the notebooks and the app, so the same cleaning rules apply everywhere.
"""
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_CSV = PROJECT_ROOT / "data" / "raw" / "pima_diabetes.csv"
OPENML_ID = 37  # https://www.openml.org/d/37

# OpenML column name -> readable name
COLUMN_NAMES = {
    "preg": "Pregnancies",
    "plas": "Glucose",           # 2-hour plasma glucose in an oral glucose tolerance test (mg/dL)
    "pres": "BloodPressure",     # diastolic blood pressure (mm Hg)
    "skin": "SkinThickness",     # triceps skinfold thickness (mm)
    "insu": "Insulin",           # 2-hour serum insulin (mu U/ml)
    "mass": "BMI",               # kg/m^2
    "pedi": "DiabetesPedigree",  # family-history score
    "age": "Age",                # years
    "class": "Outcome",          # 1 = tested positive for diabetes
}
TARGET = "Outcome"

# A value of 0 is physiologically impossible for these measurements,
# so in this dataset 0 means "not recorded".
ZERO_MEANS_MISSING = ["Glucose", "BloodPressure", "SkinThickness", "Insulin", "BMI"]

# Feature sets compared in this project
LAB_FEATURES = ["Glucose", "Insulin"]  # need a 2-hour oral glucose tolerance test
NO_LAB_FEATURES = ["Pregnancies", "BloodPressure", "SkinThickness", "BMI", "DiabetesPedigree", "Age"]
ALL_FEATURES = NO_LAB_FEATURES + LAB_FEATURES


def download_raw(path=RAW_CSV):
    """Download the dataset from OpenML and save it unchanged (original column names)."""
    from sklearn.datasets import fetch_openml

    frame = fetch_openml(data_id=OPENML_ID, as_frame=True, parser="auto").frame
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)
    return path


def load_raw(path=RAW_CSV):
    """Raw data with readable column names and a 0/1 target. Zeros are left as they are."""
    df = pd.read_csv(path).rename(columns=COLUMN_NAMES)
    df[TARGET] = (df[TARGET] == "tested_positive").astype(int)
    return df


def mark_missing(df):
    """Replace impossible zeros with NaN so they are treated as missing, not as real measurements."""
    df = df.copy()
    df[ZERO_MEANS_MISSING] = df[ZERO_MEANS_MISSING].replace(0, np.nan)
    return df


def load_clean(path=RAW_CSV):
    return mark_missing(load_raw(path))


def train_test(df, test_size=0.2, seed=42):
    """The project's single, fixed train/test split (stratified on the target).

    Every notebook uses this function, so the test set is always the same rows
    and is only looked at once, in the final evaluation.
    """
    from sklearn.model_selection import train_test_split

    return train_test_split(df, test_size=test_size, stratify=df[TARGET], random_state=seed)


if __name__ == "__main__":
    print("Saved to", download_raw())
