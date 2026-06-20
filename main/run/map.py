import folium
from main.config.config import data


def create_prediction_map(junction_df, output_file="prediction_map.html"):

    # Get average coordinates for each junction
    junction_locations = (
        data.groupby(
            ["police_station", "junction_name"]
        )
        .agg({
            "latitude": "mean",
            "longitude": "mean"
        })
        .reset_index()
    )

    # Keep only junctions that exist in historical data
    map_df = junction_df.merge(
        junction_locations,
        left_on=["police_station", "junction"],
        right_on=["police_station", "junction_name"],
        how="inner"
    )

    if map_df.empty:
        print("No valid locations found")
        return None

    def get_color(v):
        if v >= 8:
            return "red"
        elif v >= 5:
            return "orange"
        elif v >= 2:
            return "blue"
        return "green"

    m = folium.Map(
        location=[
            map_df["latitude"].mean(),
            map_df["longitude"].mean()
        ],
        zoom_start=15
    )

    # One marker per junction
    grouped = map_df.groupby(
        ["police_station", "junction"]
    )

    for (station, junction), group in grouped:

        lat = group["latitude"].iloc[0]
        lon = group["longitude"].iloc[0]

        # Peak predicted violations
        peak = group["expected_violations_here"].max()

        # Peak hour
        peak_row = group.loc[
            group["expected_violations_here"].idxmax()
        ]

        peak_hour = peak_row["hour"]

        # Hourly table
        hourly_table = """
        <table border="1" style="border-collapse:collapse;width:100%">
        <tr>
            <th>Hour</th>
            <th>Expected Violations</th>
        </tr>
        """

        for _, row in group.sort_values("hour").iterrows():

            hourly_table += f"""
            <tr>
                <td>{int(row['hour']):02d}:00</td>
                <td>{row['expected_violations_here']:.1f}</td>
            </tr>
            """

        hourly_table += "</table>"

        popup_html = f"""
        <h4>{junction}</h4>

        <b>Police Station:</b> {station}<br>
        <b>Peak Hour:</b> {int(peak_hour):02d}:00<br>
        <b>Peak Violations:</b> {peak:.1f}<br><br>

        {hourly_table}
        """

        folium.CircleMarker(
            location=[lat, lon],
            radius=max(6, peak * 2),
            color=get_color(peak),
            fill=True,
            fill_color=get_color(peak),
            fill_opacity=0.8,
            popup=folium.Popup(
                popup_html,
                max_width=500
            ),
            tooltip=(
                f"{junction} | "
                f"Peak Hour: {int(peak_hour):02d}:00 | "
                f"Peak: {peak:.1f}"
            )
        ).add_to(m)

    m.save(output_file)

    print(f"Saved map to {output_file}")

    return m