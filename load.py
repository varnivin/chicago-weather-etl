# load.py
# Loads the transformed DataFrame into SQLite or Supabase via SQLAlchemy

import logging
from sqlalchemy import create_engine, text
import pandas as pd

# ── Logger setup ──────────────────────────────────────────────────────────────
logger = logging.getLogger(__name__)

# ── Database config ───────────────────────────────────────────────────────────
# Change this to "supabase" when ready for final submission
DATABASE = "sqlite"

# Supabase connection string
# Replace with your actual Supabase URL when switching
SUPABASE_URL = "postgresql://postgres:YOUR_PASSWORD@YOUR_HOST:5432/postgres"


def get_engine():
    """
    Creates and returns a SQLAlchemy engine.
    Uses SQLite locally or Supabase for cloud deployment.

    Returns:
        sqlalchemy.engine.Engine: Database engine object.
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
    Loads the transformed DataFrame into the weather_data table.
    Replaces the table on every run for fresh API data.

    Args:
        df (pd.DataFrame): Cleaned DataFrame from transform_weather_data().
        engine: SQLAlchemy engine from get_engine().
    """
    try:
        logger.info(f"Starting data load into {DATABASE.upper()}...")

        # ── Load DataFrame into weather_data table ────────────────────────────
        # if_exists="replace" drops and recreates table on every run
        # index=False prevents Pandas adding an extra index column
        df.to_sql(
            name="weather_data",
            con=engine,
            if_exists="replace",
            index=False
        )
        logger.info(f"Successfully loaded {len(df)} rows into weather_data table.")

        # ── Verify row count after load ───────────────────────────────────────
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM weather_data"))
            row_count = result.scalar()

            if row_count != len(df):
                logger.warning(
                    f"Row count mismatch! Expected {len(df)}, found {row_count}."
                )
            else:
                logger.info(f"Verification: {row_count} rows confirmed in database. ")

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
    print("\nLoad complete! Check chicago_weather.db in your project folder.")