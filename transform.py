# transform.py
# Cleans and transforms raw API data into a database-ready DataFrame

import pandas as pd
import logging

# ── Logger setup ──────────────────────────────────────────────────────────────
logger = logging.getLogger(__name__)


def transform_weather_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans and transforms the raw API DataFrame into a
    database-ready format matching the weather_data schema.

    Args:
        df (pd.DataFrame): Raw DataFrame from extract_weather_data().

    Returns:
        pd.DataFrame: Cleaned and enriched DataFrame.

    Raises:
        Exception: If any transformation step fails.
    """

    try:
        logger.info("Starting data transformation...")

        # ── Step 1: Rename columns to match database schema ───────────────────
        df = df.rename(columns={
            "time":                          "forecast_date",
            "temperature_2m_max":            "temperature_max",
            "temperature_2m_min":            "temperature_min",
            "precipitation_sum":             "precipitation_total",
            "precipitation_probability_max": "precipitation_probability"
        })
        logger.info("Columns renamed to match database schema.")

        # ── Step 2: Convert forecast_date to proper date type ─────────────────
        df["forecast_date"] = pd.to_datetime(df["forecast_date"]).dt.date
        logger.info("forecast_date converted to date type.")

        # ── Step 3: Convert numeric columns to float ──────────────────────────
        numeric_cols = [
            "temperature_max",
            "temperature_min",
            "precipitation_total",
            "precipitation_probability"
        ]
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        logger.info("Numeric columns converted to float.")

        # ── Step 4: Fill missing values ───────────────────────────────────────
        # Precipitation defaults to 0.0 (no rain if missing)
        # Temperature filled with column median (best estimate)
        df["precipitation_total"]      = df["precipitation_total"].fillna(0.0)
        df["precipitation_probability"]  = df["precipitation_probability"].fillna(0.0)
        df["temperature_max"]            = df["temperature_max"].fillna(df["temperature_max"].median())
        df["temperature_min"]            = df["temperature_min"].fillna(df["temperature_min"].median())

        missing_count = df.isnull().sum().sum()
        logger.info(f"Missing values handled. Remaining nulls: {missing_count}")

        # ── Step 5: Round decimals to 2 places ───────────────────────────────
        for col in numeric_cols:
            df[col] = df[col].round(2)
        logger.info("Numeric columns rounded to 2 decimal places.")

        # ── Step 6: Derived column — temperature range ────────────────────────
        # Shows daily temperature swing (useful for tourism planning)
        df["temp_range"] = (df["temperature_max"] - df["temperature_min"]).round(2)
        logger.info("Derived column 'temp_range' created.")

        # ── Step 7: Derived column — weather category ─────────────────────────
        # Categorizes each day for dashboard filtering and tourism use
        def categorize_weather(row):
            if row["precipitation_probability"] >= 60:
                return "Rainy"
            elif row["temperature_max"] >= 80:
                return "Hot"
            elif row["temperature_max"] <= 32:
                return "Freezing"
            else:
                return "Mild"

        df["weather_category"] = df.apply(categorize_weather, axis=1)
        logger.info("Derived column 'weather_category' created.")

        # ── Step 8: Reorder columns to match database schema ──────────────────
        df = df[[
            "forecast_date",
            "temperature_max",
            "temperature_min",
            "precipitation_probability",
            "precipitation_total",
            "temp_range",
            "weather_category"
        ]]

        logger.info(f"Transformation complete. {len(df)} rows ready to load.")
        return df

    except KeyError as e:
        logger.error(f"Missing expected column during transform: {e}")
        raise

    except Exception as e:
        logger.error(f"Unexpected error during transformation: {e}")
        raise

    # ── Test run ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    from extract import extract_weather_data
    df_raw = extract_weather_data()
    df_clean = transform_weather_data(df_raw)
    print(df_clean)
    print(df_clean.dtypes)