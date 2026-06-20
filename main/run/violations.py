from main.config.config import model, le_station, le_day
from main.run.metadata_extractor import metadata_extractor
import numpy as np
import pandas as pd

def violations(police_station, day):
    data = metadata_extractor(police_station, day)

    predictions = np.maximum(
        0,
        np.round(model.predict(data))
    ).astype(int)

    data["police_station"] = le_station.inverse_transform(
        data["police_station"]
    )
    hours = (
        np.arctan2(data["hour_sin"], data["hour_cos"])
        * 24 / (2 * np.pi)
    ) % 24
    data["hour"] = np.round(hours).astype(int)

    days = (
        np.arctan2(data["dow_sin"], data["dow_cos"])
        * 7 / (2 * np.pi)
    ) % 7
    day_enc = np.round(days).astype(int)
    data["day"] = le_day.inverse_transform(day_enc)

    data["predictions"] = predictions

    data.drop(columns=["hour_sin","hour_cos","dow_sin","dow_cos"],inplace=True)

    return data