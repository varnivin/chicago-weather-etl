# Chicago Weather Trend Analytics — ETL Pipeline
**Developer:** Nivin Varghese | MSBA 2026
**Course:** Data Engineering
**Data Source:** Open-Meteo REST API
**Location:** Chicago, IL (41.85 N, -87.65 W)

---

## Project Overview
An end-to-end ETL pipeline that extracts daily weather data
for Chicago from the Open-Meteo API, transforms and cleans
it using Pandas, loads it into a SQLite database via
SQLAlchemy, and validates data quality with 6 automated checks.

---

## Project Structure

```
chicago_weather_etl/
├── extract.py        # Pulls data from Open-Meteo API
├── transform.py      # Cleans and enriches data
├── load.py           # Loads data into SQLite or Supabase
├── validate.py       # 6 data quality checks
├── main.py           # Runs the full pipeline
├── requirements.txt  # Required libraries
└── README.md         # This file
```

---

## Setup Instructions

### Step 1 — Clone the repository
```
git clone https://github.com/YOUR_USERNAME/chicago_weather_etl.git
cd chicago_weather_etl
```

### Step 2 — Install required libraries
```
pip install -r requirements.txt
```

### Step 3 — Run the pipeline
```
python main.py
```

That is it! The pipeline will automatically:
- Pull live weather data from the Open-Meteo API
- Clean and transform the data with Pandas
- Create chicago_weather.db automatically
- Load 28 rows into the weather_data table
- Run 6 validation checks
- Save a pipeline.log file as evidence

---

## ETL Pipeline Flow

```
Open-Meteo API → extract.py → transform.py → load.py → validate.py
```

---

## Data Variables Collected

| Column                    | Description                     | Unit       |
|---------------------------|---------------------------------|------------|
| forecast_date             | Calendar date                   | YYYY-MM-DD |
| temperature_max           | Daily maximum temperature       | F          |
| temperature_min           | Daily minimum temperature       | F          |
| precipitation_probability | Maximum rain probability        | %          |
| precipitation_total       | Total daily precipitation       | inches     |
| temp_range                | Daily temp swing (derived)      | F          |
| weather_category          | Hot/Mild/Rainy/Freezing(derived)| -          |

---

## Validation Framework

| Check               | What it validates                        |
|---------------------|------------------------------------------|
| Row Count           | 28 rows loaded as expected               |
| Null Check          | No missing values in any column          |
| Duplicate Check     | No repeated dates in the table           |
| Temperature Range   | All temps between -30F and 120F          |
| Precipitation Range | Probability 0-100, total must be >= 0    |
| Schema Check        | All 7 expected columns present           |

---

## Database

- **Type:** SQLite (local) or Supabase (cloud PostgreSQL)
- **File:** chicago_weather.db
- **Table:** weather_data
- **Rows:** 28 (14 historical + 14 forecast)
- **Switch database:** Change DATABASE = "sqlite" to
  DATABASE = "supabase" in load.py

---

## Logging

Every pipeline run generates a pipeline.log file with
timestamps for each step. This serves as evidence of
successful execution.

---

## Requirements

- Python 3.10 or higher
- See requirements.txt for full library list
- No database installation needed for SQLite