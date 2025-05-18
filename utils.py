import pandas as pd
import os
import folium 
import matplotlib.pyplot as plt
from haversine import haversine, Unit

def preprocess_bike_movements(input_csv, output_dir, city_prefix):
    df = pd.read_csv(input_csv, parse_dates=["departure_time", "arrival_time"])
    from_stations = (
        df[["from_station", "from_station_lat", "from_station_lng"]]
        .drop_duplicates()
        .reset_index(drop=True)
    )
    to_stations = (
        df[["to_station", "to_station_lat", "to_station_lng"]]
        .drop_duplicates()
        .reset_index(drop=True)
    )
    df["duration_seconds"] = (df["arrival_time"] - df["departure_time"]).dt.total_seconds()
    df = df[(df["duration_seconds"] > 0) & (df["duration_seconds"] <= 14400)]
    df["distance_meters"] = df.apply(
        lambda row: haversine(
            (row["from_station_lat"], row["from_station_lng"]),
            (row["to_station_lat"], row["to_station_lng"]),
            unit=Unit.METERS
        ),
        axis=1
    )
    os.makedirs(output_dir, exist_ok=True)
    from_stations.to_csv(os.path.join(output_dir, f"from_stations_bike_movements_{city_prefix}.csv"), index=False)
    to_stations.to_csv(os.path.join(output_dir, f"to_stations_bike_movements_{city_prefix}.csv"), index=False)
    df.to_csv(os.path.join(output_dir, f"bike_movements_{city_prefix}.csv"), index=False)
    return df, from_stations, to_stations


def plot_bike_stations_on_map(stations_df, zoom_start=12, color="blue", center=None):
    if center is not None:
        center_lat, center_lon = center
    else:
        center_lat = stations_df["latitude"].mean()
        center_lon = stations_df["longitude"].mean()
    m = folium.Map(location=[center_lat, center_lon], zoom_start=zoom_start)
    for _, row in stations_df.iterrows():
        folium.CircleMarker(
            location=[row["latitude"], row["longitude"]],
            radius=4,
            color=color,
            fill=True,
            fill_opacity=0.7,
            popup=row["station_name"]
        ).add_to(m)
    return m

def analyze_bike_movements(df):
    stats = {}
    stats["total_trips"] = len(df)
    stats["unique_stations_from"] = df["from_station"].nunique()
    stats["unique_stations_to"] = df["to_station"].nunique()
    stats["mean_duration_min"] = df["duration_seconds"].mean() / 60
    stats["median_duration_min"] = df["duration_seconds"].median() / 60
    stats["most_popular_route"] = (
        df.groupby(["from_station", "to_station"])
        .size()
        .sort_values(ascending=False)
        .head(1)
        .reset_index()[["from_station", "to_station"]]
        .values[0]
    )
    return stats


def plot_bike_speed_histogram(df, bins=50):
    speeds_kmh = (df["distance_meters"] / df["duration_seconds"]) * 3.6
    plt.figure(figsize=(8, 5))
    plt.hist(speeds_kmh, bins=bins, color="skyblue", edgecolor="black")
    plt.xlabel("Prędkość roweru [km/h]")
    plt.ylabel("Liczba przejazdów")
    plt.title("Histogram prędkości rowerów")
    plt.grid(True, alpha=0.3)
    plt.show()
    return speeds_kmh