# main.py
# Chicago Weather ETL Pipeline — Entry Point
# Run this file to execute the full pipeline:
#   python main.py

import logging
import sys
from datetime import datetime

from extract   import extract_weather_data
from transform  import transform_weather_data
from load       import get_engine, load_weather_data
from validate   import validate_weather_data

# ── Logging setup ─────────────────────────────────────────────────────────────
# Logs to both terminal AND a log file for evidence
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("pipeline.log", mode="a")
    ]
)
logger = logging.getLogger("main")


def run_pipeline():
    """
    Runs the full Chicago Weather ETL pipeline:
    Extract → Transform → Load → Validate
    """

    start_time = datetime.now()
    logger.info("================================================")
    logger.info("   Chicago Weather ETL Pipeline — STARTED")
    logger.info(f"   Run time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("================================================")

    try:

        # ── STEP 1: EXTRACT ───────────────────────────────────────────────────
        logger.info("STEP 1 — EXTRACT: Pulling data from Open-Meteo API...")
        df_raw = extract_weather_data()
        logger.info(f"STEP 1 COMPLETE — {len(df_raw)} rows extracted.")

        # ── STEP 2: TRANSFORM ─────────────────────────────────────────────────
        logger.info("STEP 2 — TRANSFORM: Cleaning and enriching data...")
        df_clean = transform_weather_data(df_raw)
        logger.info(f"STEP 2 COMPLETE — {len(df_clean)} rows transformed.")

        # ── STEP 3: LOAD ──────────────────────────────────────────────────────
        logger.info("STEP 3 — LOAD: Writing data to database...")
        engine = get_engine()
        load_weather_data(df_clean, engine)
        logger.info("STEP 3 COMPLETE — Data loaded into database.")

        # ── STEP 4: VALIDATE ──────────────────────────────────────────────────
        logger.info("STEP 4 — VALIDATE: Running quality checks...")
        all_passed = validate_weather_data(engine)

        if all_passed:
            logger.info("STEP 4 COMPLETE — All validation checks passed.")
        else:
            logger.warning("STEP 4 COMPLETE — Some validation checks failed. Review logs.")

        # ── PIPELINE SUMMARY ──────────────────────────────────────────────────
        end_time  = datetime.now()
        duration  = (end_time - start_time).seconds
        logger.info("================================================")
        logger.info("   Chicago Weather ETL Pipeline — COMPLETED")
        logger.info(f"   Rows loaded:  {len(df_clean)}")
        logger.info(f"   Duration:     {duration} seconds")
        logger.info(f"   Database:     chicago_weather.db")
        logger.info(f"   Log file:     pipeline.log")
        logger.info("================================================")

    except Exception as e:
        logger.error(f"PIPELINE FAILED: {e}")
        logger.error("Check the errors above and rerun python main.py")
        sys.exit(1)


# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    run_pipeline()