import pandas as pd
import ast
from main.config.config import multi_junction_lookup


def get_junction_breakdown(predictions_df):

    breakdown_rows = []

    for _, pred_row in predictions_df.iterrows():

        lookup_row = multi_junction_lookup[
            (multi_junction_lookup["police_station"] == pred_row["police_station"]) &
            (multi_junction_lookup["day_of_week"] == pred_row["day"]) &
            (multi_junction_lookup["is_weekend"] == pred_row["is_weekend"]) &
            (multi_junction_lookup["hour"] == pred_row["hour"])
        ]

        if lookup_row.empty:
            continue

        top_junctions = lookup_row.iloc[0]["top_junctions"]

        # If loaded from CSV, convert string to list of dicts
        if isinstance(top_junctions, str):
            top_junctions = ast.literal_eval(top_junctions)

        for junction_info in top_junctions:

            share = junction_info["share_pct"]

            breakdown_rows.append({
                "police_station": pred_row["police_station"],
                "day": pred_row["day"],
                "hour": pred_row["hour"],
                "predicted_total": pred_row["predictions"],

                "junction": junction_info["junction_name"],
                "historical_share": share,

                "expected_violations_here": round(
                    pred_row["predictions"] * share / 100,
                    1
                )
            })

    return pd.DataFrame(breakdown_rows)