import requests
import pandas as pd
import numpy as np
from main.config.config import le_day, le_station

def metadata_extractor(police_station, day):
    station_enc = le_station.transform([police_station])[0]
    day_enc = le_day.transform([day])[0]
    day = str.lower(day)

    
    lat = 12.9716
    lon = 77.5946

    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}"
        f"&longitude={lon}"
        "&hourly=temperature_2m,precipitation,cloud_cover,wind_speed_10m,weather_code"
        "&forecast_days=1"
        "&timezone=auto"
    )

    data = requests.get(url).json()

    rows = []

    for hour in range(24):
        hour_sin = np.sin(2 * np.pi * hour / 24)
        hour_cos = np.cos(2 * np.pi * hour / 24)

        dow_sin = np.sin(2 * np.pi * day_enc / 7)
        dow_cos = np.cos(2 * np.pi * day_enc / 7)
        is_weekend = int(day in ['saturday', 'sunday'])

        temperature = data["hourly"]["temperature_2m"][hour]

        rows.append({
            'police_station': station_enc,
            'is_weekend': is_weekend,
            'hour_sin': hour_sin,
            'hour_cos': hour_cos,
            'dow_sin': dow_sin,
            'dow_cos': dow_cos,
            'temperature_2m': temperature
        })

    X_pred = pd.DataFrame(rows)
    # print(X_pred)
    return X_pred
    