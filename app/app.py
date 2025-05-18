import streamlit as st
import pandas as pd
from datetime import datetime
from route_comparator import RouteComparator
from otp_client import OTPClient
from streamlit_searchbox import st_searchbox
import requests

st.set_page_config(layout="wide")
st.title("🚲 Route Comparison: Bike Sharing vs Public Transport (OTP)")

@st.cache_data
def load_data():
    bike_df = pd.read_csv("data/bike_movements_warsaw.csv")
    from_stations = pd.read_csv("data/from_stations_bike_movements_warsaw.csv")
    to_stations = pd.read_csv("data/to_stations_bike_movements_warsaw.csv")
    return bike_df, from_stations, to_stations

def nominatim_search(query):
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": query, "format": "json", "addressdetails": 1, "limit": 5}
    resp = requests.get(url, params=params, headers={"User-Agent": "streamlit-app"})
    return [
        {
            "label": r['display_name'],  # <-- Tylko to pojawi się na liście
            "lat": float(r["lat"]),
            "lon": float(r["lon"]),
        }
        for r in resp.json()
    ]

bike_df, from_stations, to_stations = load_data()
otp = OTPClient("http://localhost:8080/otp/gtfs/v1")
comparator = RouteComparator(otp, bike_df, from_stations, to_stations, radius_km=1.5)

st.subheader("1. Enter start and end addresses")
result_start = st_searchbox(nominatim_search, key="searchbox_start", placeholder="Start address...")
result_end = st_searchbox(nominatim_search, key="searchbox_end", placeholder="End address...")

if "comparison_df" not in st.session_state:
    st.session_state.comparison_df = None
if "map_generated" not in st.session_state:
    st.session_state.map_generated = False

if st.button("🔍 Compare routes") and result_start and result_end:
    try:
        start_coord = (result_start["lat"], result_start["lon"])
        end_coord = (result_end["lat"], result_end["lon"])
        when = datetime.now().astimezone().replace(hour=12, minute=0, second=0, microsecond=0)

        # Tabela porównawcza
        df = comparator.compare_as_dataframe(start_coord, end_coord, when)
        # Statyczna mapa
        comparator.draw_and_save_map_png(start_coord, end_coord, when, output_file="map.png")
        st.session_state.comparison_df = df
        st.session_state.map_generated = True
        st.success("✅ Route successfully calculated and map saved.")
    except Exception as e:
        st.error(f"Error: {e}")

if st.session_state.comparison_df is not None:
    st.subheader("2. Trip Summary")
    st.dataframe(st.session_state.comparison_df, use_container_width=True)

if st.session_state.map_generated:
    st.subheader("3. Static Map Preview")
    st.image("map.png", caption="Route map", use_column_width=True)
    with open("map.png", "rb") as file:
        st.download_button("⬇️ Download map as PNG", file, file_name="route_map.png", mime="image/png")
