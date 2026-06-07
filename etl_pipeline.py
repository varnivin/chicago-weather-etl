# =============================================================================
# etl_pipeline.py
# Chicago Weather Trend Analytics — Complete ETL Pipeline
# Developer: Nivin Varghese | MSBA 2026
# Data Source: Open-Meteo REST API
# Location: Chicago, IL (41.85 N, -87.65 W)
# Run: python etl_pipeline.py
# =============================================================================

import requests
import pandas as pd
import logging
import sys
from datetime import datetime
from sqlalchemy import create_engine, text, inspect

# ── Logging setup ─────────────────────────────────────────────────────────────
# Logs to both terminal and pipeline.log file
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("pipeline.log", mode="a")
    ]
)
logger = logging.getLogger("etl_pipeline")

# ── Database config ───────────────────────────────────────────────────────────
# Change DATABASE to "supabase" and set SUPABASE_URL for cloud deployment
# DATABASE    = "sqlite"
DATABASE    = "supabase"
SUPABASE_URL = "postgresql://postgres.mimtgltdqiequdyptkey:Chicagodatabase2026@aws-1-us-east-2.pooler.supabase.com:5432/postgres"


# =============================================================================
# SECTION 1 — EXTRACT
# Pulls daily weather data from the Open-Meteo API for Chicago, IL
# =============================================================================

def extract_weather_data() -> pd.DataFrame:
    """
    Calls the Open-Meteo API and returns raw daily weather data
    for Chicago, IL as a Pandas DataFrame.

    Returns:
        pd.DataFrame: Raw weather data with one row per day.
    """
    API_URL = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude":          41.85,
        "longitude":         -87.65,
        "daily": [
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
            "precipitation_probability_max"
        ],
        "timezone":           "auto",
        "past_days":          14,
        "forecast_days":      14,
        "temperature_unit":   "fahrenheit",
        "precipitation_unit": "inch",
        "wind_speed_unit":    "mph"
    }

    try:
        logger.info("EXTRACT: Sending request to Open-Meteo API...")
        response = requests.get(API_URL, params=params, timeout=30)
        response.raise_for_status()
        logger.info(f"EXTRACT: API response received. Status code: {response.status_code}")

        data = response.json()

        if "daily" not in data:
            raise ValueError("API response missing 'daily' key. Unexpected format.")

        df = pd.DataFrame(data["daily"])
        logger.info(f"EXTRACT: Successfully extracted {len(df)} rows from API.")
        return df

    except requests.exceptions.Timeout:
        logger.error("EXTRACT: API request timed out after 30 seconds.")
        raise
    except requests.exceptions.ConnectionError:
        logger.error("EXTRACT: Could not connect to API. Check internet connection.")
        raise
    except requests.exceptions.HTTPError as e:
        logger.error(f"EXTRACT: HTTP error from API: {e}")
        raise
    except Exception as e:
        logger.error(f"EXTRACT: Unexpected error: {e}")
        raise


# =============================================================================
# SECTION 2 — TRANSFORM
# Cleans, renames, and enriches the raw API DataFrame
# =============================================================================

def transform_weather_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans and transforms the raw API DataFrame into a
    database-ready format matching the weather_data schema.

    Args:
        df (pd.DataFrame): Raw DataFrame from extract_weather_data().

    Returns:
        pd.DataFrame: Cleaned and enriched DataFrame.
    """
    try:
        logger.info("TRANSFORM: Starting data transformation...")

        # Step 1: Rename columns to match database schema
        df = df.rename(columns={
            "time":                          "forecast_date",
            "temperature_2m_max":            "temperature_max",
            "temperature_2m_min":            "temperature_min",
            "precipitation_sum":             "precipitation_total",
            "precipitation_probability_max": "precipitation_probability"
        })
        logger.info("TRANSFORM: Columns renamed to match database schema.")

        # Step 2: Convert forecast_date to proper date type
        df["forecast_date"] = pd.to_datetime(df["forecast_date"]).dt.date
        logger.info("TRANSFORM: forecast_date converted to date type.")

        # Step 3: Convert numeric columns to float
        numeric_cols = [
            "temperature_max", "temperature_min",
            "precipitation_total", "precipitation_probability"
        ]
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        logger.info("TRANSFORM: Numeric columns converted to float.")

        # Step 4: Fill missing values
        # Precipitation defaults to 0.0 (no rain if missing)
        # Temperature filled with column median (best estimate)
        df["precipitation_total"]     = df["precipitation_total"].fillna(0.0)
        df["precipitation_probability"] = df["precipitation_probability"].fillna(0.0)
        df["temperature_max"]           = df["temperature_max"].fillna(df["temperature_max"].median())
        df["temperature_min"]           = df["temperature_min"].fillna(df["temperature_min"].median())
        logger.info(f"TRANSFORM: Missing values handled. Remaining nulls: {df.isnull().sum().sum()}")

        # Step 5: Round decimals to 2 places
        for col in numeric_cols:
            df[col] = df[col].round(2)
        logger.info("TRANSFORM: Numeric columns rounded to 2 decimal places.")

        # Step 6: Derived column — temperature range
        # Shows daily temperature swing (useful for tourism planning)
        df["temp_range"] = (df["temperature_max"] - df["temperature_min"]).round(2)
        logger.info("TRANSFORM: Derived column 'temp_range' created.")

        # Step 7: Derived column — weather category
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
        logger.info("TRANSFORM: Derived column 'weather_category' created.")

        # Step 8: Reorder columns to match database schema
        df = df[[
            "forecast_date", "temperature_max", "temperature_min",
            "precipitation_probability", "precipitation_total",
            "temp_range", "weather_category"
        ]]

        logger.info(f"TRANSFORM: Complete. {len(df)} rows ready to load.")
        return df

    except KeyError as e:
        logger.error(f"TRANSFORM: Missing expected column: {e}")
        raise
    except Exception as e:
        logger.error(f"TRANSFORM: Unexpected error: {e}")
        raise


# =============================================================================
# SECTION 3 — LOAD
# Loads transformed data into SQLite or Supabase using incremental strategy
# =============================================================================

def get_engine():
    """
    Creates and returns a SQLAlchemy engine.
    Uses SQLite locally or Supabase for cloud deployment.
    """
    try:
        if DATABASE == "supabase":
            engine = create_engine(SUPABASE_URL)
            logger.info("LOAD: Supabase engine created successfully.")
        else:
            engine = create_engine("sqlite:///chicago_weather.db", echo=False)
            logger.info("LOAD: SQLite engine created. Database: chicago_weather.db")
        return engine
    except Exception as e:
        logger.error(f"LOAD: Failed to create engine: {e}")
        raise


def load_weather_data(df: pd.DataFrame, engine) -> None:
    """
    Loads transformed DataFrame using incremental loading strategy.
    Only inserts dates not already in the database — prevents duplicates.

    Incremental loading strategy:
    - First run: creates table and loads all rows
    - Subsequent runs: checks existing dates, appends only new records
    - This prevents duplicate records when pipeline runs daily

    Args:
        df (pd.DataFrame): Cleaned DataFrame from transform_weather_data().
        engine: SQLAlchemy engine from get_engine().
    """
    try:
        logger.info(f"LOAD: Starting incremental load into {DATABASE.upper()}...")

        # Check if table exists
        inspector = inspect(engine)
        table_exists = inspector.has_table("weather_data")

        if not table_exists:
            # First run — create table and load all rows
            logger.info("LOAD: First run detected. Creating table and loading all rows...")
            df.to_sql(
                name="weather_data", con=engine,
                if_exists="replace", index=False
            )
            logger.info(f"LOAD: Initial load complete. {len(df)} rows inserted.")

        else:
            # Incremental run — only insert new dates
            logger.info("LOAD: Table exists. Checking for new dates to insert...")

            with engine.connect() as conn:
                result = conn.execute(text("SELECT forecast_date FROM weather_data"))
                existing_dates = [str(row[0]) for row in result]

            logger.info(f"LOAD: Found {len(existing_dates)} existing dates in database.")

            df["forecast_date"] = df["forecast_date"].astype(str)
            new_rows = df[~df["forecast_date"].isin(existing_dates)]

            if len(new_rows) == 0:
                logger.info("LOAD: No new dates found. Database is already up to date.")
            else:
                new_rows.to_sql(
                    name="weather_data", con=engine,
                    if_exists="append", index=False
                )
                logger.info(f"LOAD: Incremental load complete. {len(new_rows)} new rows inserted.")
                logger.info(f"LOAD: Skipped {len(df) - len(new_rows)} existing rows.")

        # Verify final row count
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM weather_data"))
            row_count = result.scalar()
            logger.info(f"LOAD: Verification — {row_count} total rows in database.")

    except Exception as e:
        logger.error(f"LOAD: Failed to load data: {e}")
        raise


# =============================================================================
# SECTION 4 — VALIDATE
# 6 data quality checks on the loaded weather_data table
# =============================================================================

def validate_weather_data(engine) -> bool:
    """
    Runs 6 data quality checks on the weather_data table.

    Checks:
        1. Row count — confirms expected number of rows loaded
        2. Null check — no missing values in any column
        3. Duplicate check — no repeated dates
        4. Temperature range — values between -30F and 120F
        5. Precipitation range — probability 0-100, total >= 0
        6. Schema check — all 7 expected columns present

    Args:
        engine: SQLAlchemy engine from get_engine().

    Returns:
        bool: True if all checks pass, False if any fail.
    """
    logger.info("VALIDATE: ====== Starting Validation Framework ======")
    passed = 0
    failed = 0

    with engine.connect() as conn:
        df = pd.read_sql(text("SELECT * FROM weather_data"), conn)

    # CHECK 1 — Row Count Verification
    # Why: Confirms API returned and loaded expected number of rows
    # Fail: Warns data may be incomplete or API returned partial data
    logger.info("VALIDATE: CHECK 1 — Row count verification...")
    actual_rows = len(df)
    if actual_rows >= 28:
        logger.info(f"VALIDATE:   PASSED — {actual_rows} rows found in database.")
        passed += 1
    else:
        logger.warning(f"VALIDATE:   FAILED — Expected 28+ rows, found {actual_rows}.")
        failed += 1

    # CHECK 2 — Null Value Check
    # Why: Null values in temperature or precipitation break dashboard charts
    # Fail: Logs which columns contain nulls for investigation
    logger.info("VALIDATE: CHECK 2 — Null value check...")
    null_counts = df.isnull().sum()
    cols_with_nulls = null_counts[null_counts > 0]
    if len(cols_with_nulls) == 0:
        logger.info("VALIDATE:   PASSED — No null values found in any column.")
        passed += 1
    else:
        logger.warning(f"VALIDATE:   FAILED — Nulls found in: {cols_with_nulls.to_dict()}")
        failed += 1

    # CHECK 3 — Duplicate Date Check
    # Why: Each date should appear exactly once — duplicates cause wrong aggregations
    # Fail: Logs the duplicate dates for investigation
    logger.info("VALIDATE: CHECK 3 — Duplicate date check...")
    duplicate_dates = df[df.duplicated(subset=["forecast_date"], keep=False)]
    if len(duplicate_dates) == 0:
        logger.info("VALIDATE:   PASSED — No duplicate dates found.")
        passed += 1
    else:
        logger.warning(f"VALIDATE:   FAILED — Duplicates: {duplicate_dates['forecast_date'].tolist()}")
        failed += 1

    # CHECK 4 — Temperature Range Validation
    # Why: Temps outside -30F to 120F are impossible for Chicago
    # Fail: Logs out-of-range rows for review
    logger.info("VALIDATE: CHECK 4 — Temperature range (-30F to 120F)...")
    temp_issues = df[
        (df["temperature_max"] < -30) | (df["temperature_max"] > 120) |
        (df["temperature_min"] < -30) | (df["temperature_min"] > 120)
    ]
    if len(temp_issues) == 0:
        logger.info("VALIDATE:   PASSED — All temperatures within valid range.")
        passed += 1
    else:
        logger.warning(f"VALIDATE:   FAILED — {len(temp_issues)} rows with invalid temperatures.")
        failed += 1

    # CHECK 5 — Precipitation Range Validation
    # Why: Probability must be 0-100 and total must be non-negative
    # Fail: Logs invalid rows for cleaning
    logger.info("VALIDATE: CHECK 5 — Precipitation range validation...")
    precip_issues = df[
        (df["precipitation_probability"] < 0)   |
        (df["precipitation_probability"] > 100) |
        (df["precipitation_total"] < 0)
    ]
    if len(precip_issues) == 0:
        logger.info("VALIDATE:   PASSED — All precipitation values within valid range.")
        passed += 1
    else:
        logger.warning(f"VALIDATE:   FAILED — {len(precip_issues)} rows with invalid precipitation.")
        failed += 1

    # CHECK 6 — Schema Validation
    # Why: Confirms all expected columns exist after loading
    # Fail: Logs missing columns so pipeline can be fixed
    logger.info("VALIDATE: CHECK 6 — Schema validation...")
    expected_cols = [
        "forecast_date", "temperature_max", "temperature_min",
        "precipitation_probability", "precipitation_total",
        "temp_range", "weather_category"
    ]
    missing_cols = [col for col in expected_cols if col not in df.columns]
    if len(missing_cols) == 0:
        logger.info("VALIDATE:   PASSED — All 7 expected columns present.")
        passed += 1
    else:
        logger.warning(f"VALIDATE:   FAILED — Missing columns: {missing_cols}")
        failed += 1

    # Summary
    logger.info("VALIDATE: ================================================")
    logger.info(f"VALIDATE: COMPLETE — {passed} passed, {failed} failed.")

    if failed == 0:
        logger.info("VALIDATE: ALL CHECKS PASSED. Data is ready for dashboard.")
        return True
    else:
        logger.warning(f"VALIDATE: {failed} check(s) failed. Review warnings above.")
        return False


# =============================================================================
# SECTION 5 — MAIN
# Orchestrates the full pipeline: Extract → Transform → Load → Validate
# =============================================================================

def run_pipeline():
    """
    Runs the complete Chicago Weather ETL Pipeline.
    Extract → Transform → Load → Validate
    """
    start_time = datetime.now()
    logger.info("================================================")
    logger.info("   Chicago Weather ETL Pipeline — STARTED")
    logger.info(f"   Run time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("================================================")

    try:
        # STEP 1 — EXTRACT
        logger.info("STEP 1 — EXTRACT: Pulling data from Open-Meteo API...")
        df_raw = extract_weather_data()
        logger.info(f"STEP 1 COMPLETE — {len(df_raw)} rows extracted.")

        # STEP 2 — TRANSFORM
        logger.info("STEP 2 — TRANSFORM: Cleaning and enriching data...")
        df_clean = transform_weather_data(df_raw)
        logger.info(f"STEP 2 COMPLETE — {len(df_clean)} rows transformed.")

        # STEP 3 — LOAD
        logger.info("STEP 3 — LOAD: Writing data to database...")
        engine = get_engine()
        load_weather_data(df_clean, engine)
        logger.info("STEP 3 COMPLETE — Data loaded into database.")

        # STEP 4 — VALIDATE
        logger.info("STEP 4 — VALIDATE: Running quality checks...")
        all_passed = validate_weather_data(engine)
        if all_passed:
            logger.info("STEP 4 COMPLETE — All validation checks passed.")
        else:
            logger.warning("STEP 4 COMPLETE — Some checks failed. Review logs.")

        # Pipeline summary
        end_time = datetime.now()
        duration = (end_time - start_time).seconds
        logger.info("================================================")
        logger.info("   Chicago Weather ETL Pipeline — COMPLETED")
        logger.info(f"   Rows in database: {len(df_clean)}")
        logger.info(f"   Duration:         {duration} seconds")
        logger.info(f"   Database:         chicago_weather.db")
        logger.info(f"   Log file:         pipeline.log")
        logger.info("================================================")

    except Exception as e:
        logger.error(f"PIPELINE FAILED: {e}")
        logger.error("Fix the error above and rerun: python etl_pipeline.py")
        sys.exit(1)


# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    run_pipeline()