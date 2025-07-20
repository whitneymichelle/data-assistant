import pandas as pd

def coerce_dates(df):
    for col in df.columns:
        # Try parsing if it's an object (likely string)
        if df[col].dtype == "object":
            try:
                converted = pd.to_datetime(df[col], errors="raise", infer_datetime_format=True)
                # Only assign if conversion looks reasonable (e.g. not 90% NaT)
                if converted.notna().mean() > 0.8:
                    df[col] = converted
            except Exception:
                continue
    return df