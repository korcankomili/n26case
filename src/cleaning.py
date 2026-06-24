import os
import pandas as pd
import duckdb

DATASETS = {
    "part_a": "data/part_a_dataset.csv",
    "part_b": "data/part_b_dataset.csv",
}


def _resolve_path(dataset: str) -> str:
    return DATASETS.get(dataset, dataset)

FUNNEL_COLS = [
    "date",
    "country",
    "marketing_channel",
    "signups",
    "kyc_init",
    "kyc_complete",
    "card_activation",
    "first_transaction",
]


def perform_data_checks(df: pd.DataFrame) -> None:
    null_counts = df.isnull().sum()
    if null_counts.sum() == 0:
        print("No missing values found.")
    else:
        print("Missing values found:")
        print(null_counts[null_counts > 0])

    if df.duplicated().sum() == 0:
        print("No duplicate rows found.")
    else:
        print("Duplicate rows found.")

    for col in df.select_dtypes(include=["number"]):
        z_scores = (df[col] - df[col].mean()) / df[col].std()
        outliers = df[abs(z_scores) > 2]
        if outliers.empty:
            print(f"No outliers in '{col}'.")
        else:
            print(f"Outliers found in '{col}': {len(outliers)} rows.")


def fix_date_column(
    df: pd.DataFrame,
    date_col: str = "date",
    drop_invalid: bool = True,
    verbose: bool = True,
) -> pd.DataFrame:
    out = df.copy()
    raw = out[date_col].astype(str).str.strip()

    # format='mixed' covers both M/D/YY and ISO YYYY-M-D; coerce bad values to NaT
    parsed = pd.to_datetime(raw, format="mixed", dayfirst=False, errors="coerce")
    bad_mask = parsed.isna()
    n_bad = int(bad_mask.sum())

    if verbose and n_bad:
        print(f"[fix_date_column] {n_bad} unparseable date(s):")
        print(raw[bad_mask].value_counts().to_string())

    out[date_col] = parsed

    if drop_invalid:
        out = out[~bad_mask].copy()
        if verbose:
            print(f"[fix_date_column] dropped {n_bad} row(s); {len(out)}/{len(df)} remain.")

    return out


def load_raw(dataset: str = "part_a") -> pd.DataFrame:
    return pd.read_csv(_resolve_path(dataset))


def clean_data(dataset: str = "part_a") -> pd.DataFrame:
    n26_funnel = load_raw(dataset)

    df_dedups = duckdb.query("""
        SELECT 
            date
            , country
            , marketing_channel
            , signups
            , kyc_init
            , kyc_complete
            , card_activation
            , first_transaction
        FROM (
            SELECT *, ROW_NUMBER() OVER (PARTITION BY date, country, marketing_channel) AS rn
            FROM n26_funnel
        )
        WHERE rn = 1
    """).to_df()

    return fix_date_column(df_dedups, date_col="date", drop_invalid=True, verbose=True)
