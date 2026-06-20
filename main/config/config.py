import joblib
import pandas as pd

MODEL_PATH = "./models/production_model.pkl"
LE_STATION_PATH = "./models/le_station.pkl"
LE_DAY_PATH = "./models/le_day.pkl"
META_DATA = "./data/metadata_lookup.csv"
MULTI_JUNCTION_LOOKUP = "./data/multi_junction_lookup.csv"
DATA = "./data/dataflipkart.csv"
VEHICLE_TYPE_SUMMARY = "./data/vehicle_type_summary.csv"

model      = joblib.load(MODEL_PATH)
le_station = joblib.load(LE_STATION_PATH)
le_day     = joblib.load(LE_DAY_PATH)
metadata = pd.read_csv(META_DATA)
multi_junction_lookup = pd.read_csv(MULTI_JUNCTION_LOOKUP)
data = pd.read_csv(DATA)
vehicle_type_summary = pd.read_csv(VEHICLE_TYPE_SUMMARY)
