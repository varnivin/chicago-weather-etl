# validate.py
# Data quality validation framework for the weather_data table

import logging
import pandas as pd
from sqlalchemy import text

# ── Logger setup ──────────────────────────────────────────────────────────────
logger = logging.getLogger(__name__)


def validate_weather_data(engine) -> bool:
    """
    Runs 6 data quality checks on the weather_data table.

    Args:
        engine: SQLAlchemy engine from get_engine().

    Returns:
        bool: True if all checks pass, False if any fail.
    """

    logger.info("====== Starting Data Validation Framework ======")
    passed = 0
    failed = 0

    # ── Load table into DataFrame for validation ──────────────────────────────
    with engine.connect() as conn:
        df = pd.read_sql(text("SELECT * FROM weather_data"), conn)

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 1 — Row Count Verification
    # Why: Confirms the API returned and loaded the expected number of rows.
    # Fail action: Warns that data may be incomplete or API returned partial data.
    # ─────────────────────────────────────────────────────────────────────────
    logger.info("CHECK 1: Row count verification...")
    expected_rows = 28
    actual_rows   = len(df)
    if actual_rows == expected_rows:
        logger.info(f"  PASSED — {actual_rows} rows found as expected.")
        passed += 1
    else:
        logger.warning(f"  FAILED — Expected {expected_rows} rows, found {actual_rows}.")
        failed += 1

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 2 — Null Value Check
    # Why: Null values in temperature or precipitation would break dashboard charts.
    # Fail action: Logs which columns contain nulls so they can be investigated.
    # ─────────────────────────────────────────────────────────────────────────
    logger.info("CHECK 2: Null value check...")
    null_counts = df.isnull().sum()
    cols_with_nulls = null_counts[null_counts > 0]
    if len(cols_with_nulls) == 0:
        logger.info("  PASSED — No null values found in any column.")
        passed += 1
    else:
        logger.warning(f"  FAILED — Null values found in: {cols_with_nulls.to_dict()}")
        failed += 1

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 3 — Duplicate Date Check
    # Why: Each date should appear exactly once. Duplicates cause wrong aggregations.
    # Fail action: Logs the duplicate dates for investigation.
    # ─────────────────────────────────────────────────────────────────────────
    logger.info("CHECK 3: Duplicate date check...")
    duplicate_dates = df[df.duplicated(subset=["forecast_date"], keep=False)]
    if len(duplicate_dates) == 0:
        logger.info("  PASSED — No duplicate dates found.")
        passed += 1
    else:
        logger.warning(f"  FAILED — Duplicate dates found: {duplicate_dates['forecast_date'].tolist()}")
        failed += 1

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 4 — Temperature Range Validation
    # Why: Temperatures outside -30F to 120F are physically impossible for Chicago.
    # Fail action: Logs the out-of-range rows for review.
    # ─────────────────────────────────────────────────────────────────────────
    logger.info("CHECK 4: Temperature range validation (-30F to 120F)...")
    temp_issues = df[
        (df["temperature_max"] < -30) | (df["temperature_max"] > 120) |
        (df["temperature_min"] < -30) | (df["temperature_min"] > 120)
    ]
    if len(temp_issues) == 0:
        logger.info("  PASSED — All temperatures within valid range.")
        passed += 1
    else:
        logger.warning(f"  FAILED — {len(temp_issues)} rows with out-of-range temperatures.")
        failed += 1

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 5 — Precipitation Range Validation
    # Why: Probability must be 0-100 and total precipitation must be non-negative.
    # Fail action: Logs the invalid rows so they can be cleaned.
    # ─────────────────────────────────────────────────────────────────────────
    logger.info("CHECK 5: Precipitation range validation...")
    precip_issues = df[
        (df["precipitation_probability"] < 0)   |
        (df["precipitation_probability"] > 100) |
        (df["precipitation_total"] < 0)
    ]
    if len(precip_issues) == 0:
        logger.info("  PASSED — All precipitation values within valid range.")
        passed += 1
    else:
        logger.warning(f"  FAILED — {len(precip_issues)} rows with invalid precipitation values.")
        failed += 1

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 6 — Schema Validation
    # Why: Confirms all expected columns exist after loading.
    # Fail action: Logs which columns are missing so the pipeline can be fixed.
    # ─────────────────────────────────────────────────────────────────────────
    logger.info("CHECK 6: Schema validation...")
    expected_cols = [
        "forecast_date", "temperature_max", "temperature_min",
        "precipitation_probability", "precipitation_total",
        "temp_range", "weather_category"
    ]
    missing_cols = [col for col in expected_cols if col not in df.columns]
    if len(missing_cols) == 0:
        logger.info("  PASSED — All 7 expected columns present.")
        passed += 1
    else:
        logger.warning(f"  FAILED — Missing columns: {missing_cols}")
        failed += 1

    # ── Summary ───────────────────────────────────────────────────────────────
    logger.info("================================================")
    logger.info(f"VALIDATION COMPLETE: {passed} passed, {failed} failed.")

    if failed == 0:
        logger.info("ALL CHECKS PASSED. Data is ready for dashboard.")
        return True
    else:
        logger.warning(f"{failed} validation check(s) failed. Review warnings above.")
        return False


# ── Test run ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    from load import get_engine
    engine = get_engine()
    validate_weather_data(engine)
