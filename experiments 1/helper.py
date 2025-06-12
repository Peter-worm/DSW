from scipy.stats import zscore
import numpy as np
import pandas as pd

def find_outlier_stations(unique_from_station_coords, threshold=3):
    """
    Identify outlier stations based on z-score of their coordinates.
    Returns a DataFrame of outlier stations.
    """
    coords = unique_from_station_coords[['from_station_lat', 'from_station_lng']].values
    z_scores = zscore(coords)
    z_norm = np.linalg.norm(z_scores, axis=1)
    outlier_indices = np.where(z_norm > threshold)[0]
    outlier_stations = unique_from_station_coords.iloc[outlier_indices]
    return outlier_stations

# Create a dictionary that maps (from_station_lat, from_station_lng) to from_station name
def create_station_location_mapping(df):
    location_to_station = {}
    station_to_location = {}
    for _, row in df.iterrows():
        key = (row['from_station_lat'], row['from_station_lng'])
        # Only set if not already present to avoid overwriting with possibly different names for same coords
        if key not in location_to_station:
            location_to_station[key] = row['from_station']

    for key, station in location_to_station.items():
        station_to_location[station] = key
    return location_to_station, station_to_location