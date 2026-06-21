# FR2 — Parking-Induced Congestion Intelligence

**Flipkart Gridlock Hackathon — Round 2 Submission**

Live demo: https://fr2-n2sg.onrender.com/

## Problem Statement

Poor Visibility on Parking-Induced Congestion

On-street illegal parking and spillover parking near commercial areas, metro
stations, and events choke carriageways and intersections. Enforcement today
is patrol-based and reactive, there is no heatmap of parking violations
versus their actual congestion impact, and it is difficult to prioritize
which zones need enforcement attention first.

**Problem statement direction:** How can AI-driven parking intelligence
detect illegal parking hotspots and quantify their impact on traffic flow
to enable targeted enforcement?

## What This Project Does

Given just a **police station** and a **day of the week**, the system
produces a full operational dispatch schedule for that station, answering
four questions a traffic enforcement supervisor actually needs answered
every morning:

1. **When** are violations likely to spike, hour by hour
2. **Where** within that station's jurisdiction (which junction)
3. **How severe** is the likely congestion impact, not just the violation count
4. **How many officers**, and whether a tow truck is needed, for each window

The system is built on Bengaluru's anonymized parking violation dataset
(Jan–May 2024, ~298K records) supplied for the hackathon, enriched with
historical weather data (Open-Meteo) and engineered time-series features.

## Model Performance

The XGBoost violation-count model was evaluated using a **chronological**
train/test split (last ~20% of the timeline held out), so reported numbers
reflect genuine forward-looking accuracy rather than leakage between nearby
timestamps.

| Metric | Value |
|---|---|
| MAE (Mean Absolute Error) | 1.62 violations |
| Peak Score (within ±5 of actual) | 92.6% |
| Peak-Aware Score (stricter tolerance on high-violation hours) | 81.1% |
| Tolerance Accuracy (±10) | 96.8% |
| Tolerance Accuracy (±19) | 99.0% |

Since the operational goal is identifying *when and where to deploy
officers* rather than predicting an exact violation count, tolerance-based
accuracy (how often the prediction falls within a usable range of the
actual count) is treated as the primary evaluation metric, alongside the
Peak-Aware Score, which specifically measures accuracy on high-violation
hours — the windows that actually matter for dispatch decisions.

Top model features by importance: `hour` (cyclical encoding), `police_station`,
`is_weekend`, and `temperature_2m` — confirming that time-of-day and station
identity are the dominant drivers of violation volume, with weather acting as
a meaningful secondary signal (violations drop by roughly 66% during rainfall
in the historical data).

## How It Works

```
Police Station + Day of Week  (user input)
        |
        v
XGBoost model -> predicted violation count per hour
        |
        v
Historical lookup -> junction breakdown, vehicle type mix,
                      lat/lon, center code  (per station + hour)
        |
        v
Severity scoring -> officers needed, tow truck recommendation,
                     congestion impact score
        |
        v
Streamlit dashboard -> heatmap, trend charts, junction ranking,
                        vehicle activity, full schedule table
```

### Modeling notes

- The dataset's `closed_datetime` and `action_taken_timestamp` fields were
  100% null across all records — this was treated as a finding in itself
  (the data confirms there is no closed-loop enforcement feedback today,
  which is part of the problem this project addresses) rather than a data
  quality issue to paper over.
- The training data was reconstructed as a complete hourly timeline per
  station (including zero-violation hours), since the raw violation log
  only contains rows where an officer actually logged an incident. Without
  this correction, the model would never learn what a "quiet" hour looks
  like.
- Train/test split is chronological (not random), so reported accuracy
  reflects genuine forward-looking performance rather than leakage between
  nearby timestamps.
- Junction and vehicle-type assignment for a given station/hour use
  historical share rather than a forced single prediction, since several
  station/hour combinations have no single dominant junction.

## Repository Structure

```
FR2/
├── app.py                  # Streamlit dashboard entry point
├── main/
│   ├── run/
│   │   ├── violations.py   # loads model, runs hourly violation prediction
│   │   └── junction.py     # junction + vehicle composition breakdown
│   └── config/
│       └── config.py       # loads cleaned data and lookup tables
├── models/                 # trained XGBoost model + encoders (.pkl)
├── data/                   # cleaned dataset and precomputed lookup tables
├── notebooks/              # EDA, feature engineering, model training notebooks
└── requirements.txt
```

## How to Run Locally

### Prerequisites

- Python 3.10 or later
- pip

### Setup

```bash
# 1. Clone the repository
git clone https://github.com/reddyrohith49471/FR2.git
cd FR2

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # on Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
streamlit run app.py
```

The app will open automatically in your browser, typically at
`http://localhost:8501`.

### Using the Dashboard

1. Select a **Police Station** from the sidebar dropdown.
2. The dashboard defaults to predictions for **today's day of week** —
   optionally narrow further using the **Junction** and **Hour** filters
   in the sidebar.
3. Review the dashboard top to bottom:
   - **Historical Violation Locations** — map of past violations for the
     selected station/day/filters
   - **Hourly Violation Trend** — shape of the predicted day at a glance
   - **Vehicle Type Activity** — which vehicle types are historically
     active at which hours
   - **Junction Comparison** — total predicted violations by junction
   - **Violation Intensity Heatmap** — hour vs junction at a glance
   - **Full Detailed Table** (expandable) — the complete underlying
     prediction data, including historical share per junction

No login or configuration is required — the model and lookup tables are
pre-trained and bundled with the repository.

## Tech Stack

- **Modeling:** Python, pandas, NumPy, XGBoost, scikit-learn
- **Weather enrichment:** Open-Meteo historical weather API
- **Dashboard:** Streamlit, Plotly, Folium / streamlit-folium
- **Deployment:** Render
