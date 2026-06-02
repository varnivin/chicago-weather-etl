# load.py
# Loads transformed DataFrame into SQLite or Supabase via SQLAlchemy
# Uses incremental loading — only inserts new dates, skips existing ones

import logging
import pandas as pd
from sqlalchemy import create_engine, text, inspect

# ── Logger setup ──────────────────────────────────────────────────────────────
logger = logging.getLogger(__name__)

# ── Database config ───────────────────────────────────────────────────────────
# Change to "supabase" when ready for final submission
DATABASE = "sqlite"

# Replace with your actual Supabase URL when switching
SUPABASE_URL = "postgresql://postgres:YOUR_PASSWORD@YOUR_HOST:5432/postgres"


def get_engine():
    """
    Creates and returns a SQLAlchemy engine.
    Uses SQLite locally or Supabase for cloud deployment.
    """
    try:
        if DATABASE == "supabase":
            engine = create_engine(SUPABASE_URL)
            logger.info("Supabase engine created successfully.")
        else:
            engine = create_engine("sqlite:///chicago_weather.db", echo=False)
            logger.info("SQLite engine created. Database: chicago_weather.db")
        return engine

    except Exception as e:
        logger.error(f"Failed to create database engine: {e}")
        raise


def load_weather_data(df: pd.DataFrame, engine) -> None:
    """
    Loads transformed DataFrame into weather_data table using
    incremental loading — only inserts dates not already in the database.

    Args:
        df (pd.DataFrame): Cleaned DataFrame from transform_weather_data().
        engine: SQLAlchemy engine from get_engine().
    """
    try:
        logger.info(f"Starting incremental load into {DATABASE.upper()}...")

        # ── Check if table exists ─────────────────────────────────────────────
        inspector = inspect(engine)
        table_exists = inspector.has_table("weather_data")

        if not table_exists:
            # ── First run — create table and load all rows ────────────────────
            logger.info("Table does not exist. Creating and loading all rows...")
            df.to_sql(
                name="weather_data",
                con=engine,
                if_exists="replace",
                index=False
            )
            logger.info(f"Initial load complete. {len(df)} rows inserted.")

        else:
            # ── Incremental run — only insert new dates ───────────────────────
            logger.info("Table exists. Checking for new dates to insert...")

            # Get existing dates from database
            with engine.connect() as conn:
                result = conn.execute(text("SELECT forecast_date FROM weather_data"))
                existing_dates = [str(row[0]) for row in result]

            logger.info(f"Found {len(existing_dates)} existing dates in database.")

            # Filter to only new rows not already in database
            df["forecast_date"] = df["forecast_date"].astype(str)
            new_rows = df[~df["forecast_date"].isin(existing_dates)]

            if len(new_rows) == 0:
                logger.info("No new dates found. Database is already up to date.")
            else:
                # Insert only the new rows
                new_rows.to_sql(
                    name="weather_data",
                    con=engine,
                    if_exists="append",
                    index=False
                )
                logger.info(f"Incremental load complete. {len(new_rows)} new rows inserted.")
                logger.info(f"Skipped {len(df) - len(new_rows)} existing rows.")

        # ── Verify final row count ────────────────────────────────────────────
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM weather_data"))
            row_count = result.scalar()
            logger.info(f"Verification: {row_count} total rows in database.")

    except Exception as e:
        logger.error(f"Failed to load data into database: {e}")
        raise


# ── Test run ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    from extract import extract_weather_data
    from transform import transform_weather_data

    df_raw   = extract_weather_data()
    df_clean = transform_weather_data(df_raw)
    engine   = get_engine()
    load_weather_data(df_clean, engine)
    print("\nLoad complete!")