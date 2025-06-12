from scipy.stats import zscore
import numpy as np
import pandas as pd
import pickle

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


def load_trip_data():
    """
    Loads trip data from CSV and pickle files.

    Returns:
        trips_that_didnt_go_anywhere (pd.DataFrame): DataFrame loaded from CSV.
        trips_that_went_somewhere (list): List loaded from pickle.
        other_errors (list): List loaded from pickle.
    """
    trips_that_didnt_go_anywhere = pd.read_csv('otp_trips_data_for_bikes\\trips_that_didnt_go_anywhere.csv')
    with open('otp_trips_data_for_bikes\\trips_that_went_somewhere.pkl', 'rb') as f:
        trips_that_went_somewhere = pickle.load(f)
    with open('otp_trips_data_for_bikes\\other_errors.pkl', 'rb') as f:
        other_errors = pickle.load(f)
    return trips_that_didnt_go_anywhere, trips_that_went_somewhere, other_errors




def get_warsaw_stations_coords(d):
    
    warsaw_bike_movements = pd.read_csv('..\\bike_movements_warsaw.csv')
    location_to_station, station_to_location = create_station_location_mapping(warsaw_bike_movements)
    unique_from_station_coords = warsaw_bike_movements[['from_station_lat', 'from_station_lng']].drop_duplicates()
    outlier_stations = find_outlier_stations(unique_from_station_coords)
    outlier_coords = [tuple(x) for x in outlier_stations[['from_station_lat', 'from_station_lng']].values]
    no_outlier_stations_coords = [x for x in location_to_station.keys() if x not in outlier_coords]
    return no_outlier_stations_coords