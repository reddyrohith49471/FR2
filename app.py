import streamlit as st
from streamlit_folium import st_folium
import folium
import plotly.express as px
import pandas as pd
from datetime import datetime

from main.run.violations import violations
from main.run.junction import get_junction_breakdown
from main.config.config import data, vehicle_type_summary



# PAGE CONFIG


st.set_page_config(
    page_title="Traffic Violation Dashboard",
    layout="wide"
)


# HELPERS


def time_label(h):
    h = int(h)
    suffix = 'am' if h < 12 else 'pm'
    hr = 12 if h % 12 == 0 else h % 12
    return f"{hr}:00 {suffix}"



# CACHED TRANSFORMATIONS


@st.cache_data(show_spinner=False)
def get_predictions(station, day):
    pred = violations(station, day)
    df = get_junction_breakdown(pred)

    df["hour"] = df["hour"].astype(int)
    df["expected_violations_here"] = (
        df["expected_violations_here"]
        .round()
        .astype(int)
    )

    df["Time"] = df["hour"].apply(time_label)

    return df


@st.cache_data(show_spinner=False)
def get_map_points(station, day, junction, hour):

    filtered = data[
        (data["police_station"] == station)
        &
        (data["day_of_week"] == day)
    ]

    if junction != "All Junctions":
        filtered = filtered[
            filtered["junction_name"] == junction
        ]

    if hour != "All Hours":
        temp = filtered[
            filtered["hour"] == hour
        ]

        if not temp.empty:
            filtered = temp

    return (
        filtered
        .groupby(["latitude", "longitude"])
        .size()
        .reset_index(name="count")
    )


@st.cache_data(show_spinner=False)
def get_hourly_totals(df):
    return (
        df.groupby(["hour", "Time"])
        .agg(
            Total_Violations=(
                "expected_violations_here",
                "sum"
            )
        )
        .reset_index()
        .sort_values("hour")
    )


@st.cache_data(show_spinner=False)
def get_junction_totals(df):
    return (
        df.groupby("junction")
        .agg(
            Total_Violations=(
                "expected_violations_here",
                "sum"
            )
        )
        .reset_index()
        .sort_values(
            "Total_Violations",
            ascending=True
        )
    )


@st.cache_data(show_spinner=False)
def get_heatmap_matrix(df):

    pivot = df.pivot_table(
        index="junction",
        columns="Time",
        values="expected_violations_here",
        aggfunc="sum",
        fill_value=0
    )

    hour_order = (
        df[["hour", "Time"]]
        .drop_duplicates()
        .sort_values("hour")["Time"]
        .tolist()
    )

    pivot = pivot.reindex(
        columns=hour_order,
        fill_value=0
    )

    pivot = pivot.loc[
        pivot.sum(axis=1)
        .sort_values(ascending=False)
        .index
    ]

    return pivot


@st.cache_data(show_spinner=False)
def get_junction_hourly(df, junction):

    return (
        df[df["junction"] == junction]
        .groupby(["hour", "Time"])
        .agg(
            Expected_Violations=(
                "expected_violations_here",
                "sum"
            )
        )
        .reset_index()
        .sort_values("hour")
    )


@st.cache_data(show_spinner=False)
def get_vehicle_heatmap(station, day, junction, hour):
    """Return a vehicle-type × hour pivot of actual spotted counts.

    Each cell = number of violation records (spots) for that vehicle
    type in that hour, filtered to the selected station, day,
    junction, and hour.
    Uses the raw `data` DataFrame which has one row per record.
    """
    df = data[
        (data["police_station"] == station)
        &
        (data["day_of_week"] == day)
    ]

    if junction != "All Junctions":
        temp = df[df["junction_name"] == junction]
        if not temp.empty:
            df = temp

    if hour != "All Hours":
        temp = df[df["hour"] == hour]
        if not temp.empty:
            df = temp

    counts = (
        df.groupby(["hour", "vehicle_type"])
        .size()
        .reset_index(name="Times Spotted")
    )

    pivot = counts.pivot(
        index="vehicle_type",
        columns="hour",
        values="Times Spotted"
    ).fillna(0)

    pivot.columns = [time_label(h) for h in pivot.columns]

    pivot = pivot.loc[
        pivot.sum(axis=1).sort_values(ascending=False).index
    ]

    return pivot



# TODAY


today = datetime.now().strftime("%A")

st.title("🚦 Traffic Violation Prediction Dashboard")
st.info(f"Predictions for {today}")


# SIDEBAR


police_station = st.sidebar.selectbox(
    "Police Station",
    sorted(data["police_station"].dropna().unique())
)


# PREDICTIONS  (junction_df is the SINGLE source of truth from here on)


junction_df = get_predictions(
    police_station,
    today
)


# FILTERS


junction_options = sorted(junction_df["junction"].dropna().unique())

junction = st.sidebar.selectbox(
    "Junction",
    ["All Junctions"] + list(junction_options)
)

hour = st.sidebar.selectbox(
    "Hour",
    ["All Hours"] + list(range(24))
)


# MAP — historical violation density


st.subheader("📍 Historical Violation Locations")

unique_points = get_map_points(
    police_station,
    today,
    junction,
    hour
)

if unique_points.empty:
    st.warning("No historical data found.")
else:
    center_lat = unique_points["latitude"].mean()
    center_lon = unique_points["longitude"].mean()

    m = folium.Map(location=[center_lat, center_lon], zoom_start=16)

    for _, row in unique_points.iterrows():
        folium.CircleMarker(
            location=[row["latitude"], row["longitude"]],
            radius=min(8, max(2, row["count"] // 5)),
            fill=True,
            popup=f"Count: {row['count']}"
        ).add_to(m)

    st_folium(m, width=1400, height=650)


# PLOT 1: HOURLY TREND — shape of the day at a glance


st.subheader(f"📈 Hourly Violation Trend — {police_station} | {today}")

hourly_totals = get_hourly_totals(
    junction_df
)

fig_trend = px.area(
    hourly_totals,
    x="Time",
    y="Total_Violations",
    labels={"Time": "Hour of Day", "Total_Violations": "Expected Violations"},
    markers=True,
)
fig_trend.update_xaxes(
    categoryorder="array",
    categoryarray=hourly_totals.sort_values("hour")["Time"].tolist(),
)
fig_trend.update_layout(height=350, margin=dict(l=10, r=10, t=20, b=10))

st.plotly_chart(fig_trend, use_container_width=True)

if junction != "All Junctions":

    st.subheader(
        f"📍 Junction Hourly Trend — {junction}"
    )

    junction_hourly = get_junction_hourly(
        junction_df,
        junction
    )

    fig_junction_trend = px.area(
        junction_hourly,
        x="Time",
        y="Expected_Violations",
        markers=True
    )

    fig_junction_trend.update_xaxes(
        categoryorder="array",
        categoryarray=junction_hourly["Time"].tolist()
    )

    fig_junction_trend.update_layout(
        height=350,
        margin=dict(
            l=10,
            r=10,
            t=20,
            b=10
        )
    )

    st.plotly_chart(
        fig_junction_trend,
        use_container_width=True
    )



# VEHICLE TYPE HEATMAP — which vehicles appear by hour


junction_label = junction if junction != "All Junctions" else "All Junctions"
st.subheader(f"🚗 Vehicle Type Activity — {police_station} | {junction_label} | {today}")

vehicle_pivot = get_vehicle_heatmap(
    police_station,
    today,
    junction,
    hour
)

if vehicle_pivot.empty:
    st.warning("No vehicle type data for the selected filters.")
else:
    fig_veh = px.imshow(
        vehicle_pivot,
        labels=dict(x="Hour", y="Vehicle Type", color="Times Spotted"),
        aspect="auto",
        color_continuous_scale="Viridis",
    )
    fig_veh.update_traces(xgap=1, ygap=1)
    fig_veh.update_layout(
        height=max(300, len(vehicle_pivot) * 30),
        margin=dict(l=10, r=10, t=20, b=10),
    )
    st.plotly_chart(fig_veh, use_container_width=True)


# PLOT 2: JUNCTION COMPARISON — where to focus, station-wide


st.subheader("🚧 Junction Comparison — Total Violations Today")

junction_totals = get_junction_totals(
    junction_df
)

fig_junction = px.bar(
    junction_totals,
    x="Total_Violations",
    y="junction",
    orientation="h",
    labels={"Total_Violations": "Expected Violations", "junction": "Junction"},
)
fig_junction.update_layout(
    height=max(300, len(junction_totals) * 35),
    margin=dict(l=10, r=10, t=20, b=10),
)

st.plotly_chart(fig_junction, use_container_width=True)


# PLOT 3: HOUR x JUNCTION HEATMAP — when AND where together


st.subheader("🔥 Violation Intensity — Hour vs Junction")

pivot = get_heatmap_matrix(
    junction_df
)

fig_heat = px.imshow(
    pivot,
    labels=dict(x="Hour", y="Junction", color="Expected Violations"),
    aspect="auto",
    color_continuous_scale="YlOrRd",
)
fig_heat.update_traces(xgap=1, ygap=1)
fig_heat.update_layout(height=max(350, len(pivot) * 30), margin=dict(l=10, r=10, t=20, b=10))

st.plotly_chart(fig_heat, use_container_width=True)



# RAW DATA — kept available, but collapsed by default


with st.expander("📋 View Full Detailed Table"):
    display_df = junction_df.copy()

    if junction != "All Junctions":
        display_df = display_df[display_df["junction"] == junction]

    if hour != "All Hours":
        display_df = display_df[display_df["hour"] == hour]

    display_df = display_df.sort_values(
        ["hour", "expected_violations_here"], ascending=[True, False]
    )[[
        "Time",
        "junction",
        "historical_share",
        "expected_violations_here"
    ]].rename(columns={
        "junction": "Junction",
        "historical_share": "Historical Share %",
        "expected_violations_here": "Expected Violations"
    })

    st.dataframe(display_df, use_container_width=True, hide_index=True)