# Chicago Weather Intelligence — ETL Pipeline and Dashboard
**Developer:** Nivin Varghese | MSBA 2026
**Course:** Data Engineering
**Data Source:** Open-Meteo REST API
**Location:** Chicago, IL (41.85 N, -87.65 W)

## Project Overview
An end-to-end data engineering project that extracts daily weather data for Chicago from the Open-Meteo API, transforms and cleans it using Pandas, loads it into a Supabase PostgreSQL database via SQLAlchemy, validates data quality with 6 automated checks, and presents insights through an interactive Plotly Dash dashboard designed for residents, tourists, commuters and farmers.

## Project Structure
chicago_weather_etl/
├── etl_pipeline.py   # Complete ETL workflow in one script
├── extract.py        # Pulls data from Open-Meteo API
├── transform.py      # Cleans and enriches data
├── load.py           # Loads data into SQLite or Supabase
├── validate.py       # 6 data quality checks
├── main.py           # Runs the full pipeline
├── dashboard.py      # Dash dashboard submission version
├── dashboard_v4.py   # Dash dashboard full featured version
├── requirements.txt  # Required libraries
└── README.md         # This file

## Setup Instructions

### Step 1 — Clone the repository
git clone https://github.com/varnivin/chicago-weather-etl.git
cd chicago-weather-etl

### Step 2 — Install required libraries
pip install -r requirements.txt

### Step 3 — Run the ETL pipeline
python etl_pipeline.py

The pipeline will automatically:
- Pull live weather data from the Open-Meteo API
- Clean and transform the data with Pandas
- Load 28 rows into the Supabase PostgreSQL database
- Run 6 validation checks
- Save a pipeline.log file as evidence

### Step 4 — Run the dashboard
python dashboard_v4.py

Open your browser and go to:
http://127.0.0.1:8050

## ETL Pipeline Flow
Open-Meteo API
      |
extract.py    — Pulls live weather data via REST API
      |
transform.py  — Cleans, renames columns, adds derived metrics
      |
load.py       — Incremental load into Supabase PostgreSQL
      |
validate.py   — 6 automated data quality checks
      |
dashboard_v4.py — Interactive Plotly Dash dashboard

## Data Variables Collected

| Column                    | Description                      | Unit       |
|---------------------------|----------------------------------|------------|
| forecast_date             | Calendar date                    | YYYY-MM-DD |
| temperature_max           | Daily maximum temperature        | F          |
| temperature_min           | Daily minimum temperature        | F          |
| precipitation_probability | Maximum rain probability         | %          |
| precipitation_total       | Total daily precipitation        | inches     |
| temp_range                | Daily temp swing (derived)       | F          |
| weather_category          | Hot/Mild/Rainy/Freezing (derived)| -          |

## Validation Framework

| Check               | What it validates                     | Why it matters                        |
|---------------------|---------------------------------------|---------------------------------------|
| Row Count           | 28 rows loaded as expected            | Confirms full API response received   |
| Null Check          | No missing values in any column       | Prevents broken dashboard charts      |
| Duplicate Check     | No repeated dates in the table        | Ensures incremental loading is clean  |
| Temperature Range   | All temps between -30F and 120F       | Catches physically impossible values  |
| Precipitation Range | Probability 0-100, total >= 0         | Validates API data integrity          |
| Schema Check        | All 7 expected columns present        | Confirms table structure is correct   |

## Database

Primary: Supabase PostgreSQL (cloud hosted)
- Live data is loaded and queried directly from Supabase
- Connection managed via SQLAlchemy and psycopg2
- Table: weather_data
- Rows: 28 (14 historical + 14 forecast, updates daily)

Fallback: SQLite (local)
- If Supabase is unavailable the pipeline falls back to chicago_weather.db
- To switch: Change DATABASE = "supabase" to DATABASE = "sqlite" in etl_pipeline.py

## Incremental Loading Strategy
The pipeline uses incremental loading. On every run it checks which dates already exist in the database and only inserts new dates. This prevents duplicate records and keeps the database clean across daily automated runs.

First run   : Creates table and loads all 28 rows
Daily runs  : Checks existing dates and inserts only new dates
Duplicates  : Zero — enforced by incremental logic

## Dashboard Features

The interactive dashboard (dashboard_v4.py) includes:

Header
- Animated sky gradient background
- Dynamic weather animation that changes based on today's category
- Spinning sun for Hot, falling rain drops for Rainy, swaying cloud for Mild, falling snowflakes for Freezing

KPI Cards
- 6 circle cards: Peak Temp, Lowest Temp, Avg Precipitation, Hot Days, Rainy Days, Mild Days
- Grow animation on hover

Filters
- Segmented tab bar: All, Hot, Mild, Rainy, Freezing
- Date range slider to zoom into any period
- Both filters work together and update all charts live

Charts
- Temperature trend: max and min lines with shaded range area and Today marker
- Daily precipitation bar chart
- Weather category donut chart

Smart Insight Panels
- Traffic and Commute: best commute days, rain risk alerts, wet road warnings, heat advisories
- Agriculture and Farming: frost risk alerts, irrigation needs, rainfall totals, optimal planting windows
- Tourism and Outdoors: best days for Downtown, Navy Pier, Millennium Park, O'Hare and Midway airports

## Business Insights
Chicago experiences significant seasonal weather changes. This dashboard helps four target audiences:

- Residents plan daily commutes around rain and heat advisories
- Tourists identify the best days to visit Navy Pier, Millennium Park and Downtown Chicago
- Farmers monitor frost risk, rainfall totals and optimal planting windows
- Airport travelers anticipate weather delays at O'Hare and Midway

## Logging
Every pipeline run generates a pipeline.log file with timestamps for each step. This serves as evidence of successful execution and supports reproducibility requirements.

## Requirements
- Python 3.10 or higher
- Supabase account free tier or local SQLite fallback
- See requirements.txt for full library list