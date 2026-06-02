# extract.py
# Pulls daily weather data from the Open-Meteo API for Chicago, IL

import requests
import pandas as pd
import logging

# ── Logger setup ──────────────────────────────────────────────────────────────
logger = logging.getLogger(__name__)


def extract_weather_data() -> pd.DataFrame:
    """
    Calls the Open-Meteo API and returns raw daily weather data
    for Chicago, IL as a Pandas DataFrame.

    Returns:
        pd.DataFrame: Raw weather data with one row per day.

    Raises:
        Exception: If the API call fails or returns unexpected data.
    """

    # ── API configuration ─────────────────────────────────────────────────────
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
        logger.info("Sending request to Open-Meteo API...")
        response = requests.get(API_URL, params=params, timeout=30)

        # ── Validate HTTP response ────────────────────────────────────────────
        response.raise_for_status()
        logger.info(f"API response received. Status code: {response.status_code}")

        # ── Parse JSON ────────────────────────────────────────────────────────
        data = response.json()

        if "daily" not in data:
            raise ValueError("API response missing 'daily' key. Unexpected format.")

        # ── Convert to DataFrame ──────────────────────────────────────────────
        df = pd.DataFrame(data["daily"])
        logger.info(f"Extracted {len(df)} rows from API response.")

        return df

    except requests.exceptions.Timeout:
        logger.error("API request timed out after 30 seconds.")
        raise

    except requests.exceptions.ConnectionError:
        logger.error("Could not connect to Open-Meteo API. Check your internet connection.")
        raise

    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error from API: {e}")
        raise

    except Exception as e:
        logger.error(f"Unexpected error during extraction: {e}")
        raise

    # ── Test run ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    df = extract_weather_data()
    print(df)