from datetime import datetime
from typing import Tuple
import pandas as pd
import folium
from geopy.distance import geodesic
import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import tempfile

Coord = Tuple[float, float]

class RouteComparator:
    def __init__(self, otp_client, bike_df, from_stations, to_stations, radius_km=1.0):
        self.otp_client = otp_client
        self.bike_df = bike_df
        self.from_stations = from_stations
        self.to_stations = to_stations
        self.radius_km = radius_km

    def find_stations_within_radius(self, lat, lon, stations_df, lat_col, lon_col):
        ref_point = (lat, lon)
        stations_df = stations_df.copy()
        stations_df["distance"] = stations_df.apply(
            lambda row: geodesic(ref_point, (row[lat_col], row[lon_col])).km, axis=1
        )
        return stations_df[stations_df["distance"] <= self.radius_km]

    def compare_summary(self, start_coord: Coord, end_coord: Coord, when: datetime) -> dict:
        otp_itinerary = self.otp_client.fastest_connection(when, start_coord, end_coord)
        otp_duration = otp_itinerary["duration"]
        modes = {leg["mode"] for leg in otp_itinerary["legs"]}

        if modes == {"WALK"}:
            return {
                "otp_duration_min": otp_duration / 60,
                "note": "OTP returned only WALK mode. Skipping bike suggestion."
            }

        nearby_starts = self.find_stations_within_radius(
            start_coord[0], start_coord[1], self.from_stations, "from_station_lat", "from_station_lng"
        )
        nearby_ends = self.find_stations_within_radius(
            end_coord[0], end_coord[1], self.to_stations, "to_station_lat", "to_station_lng"
        )

        if nearby_starts.empty or nearby_ends.empty:
            return {"error": "No bike stations nearby."}

        start_station = nearby_starts.iloc[0]
        end_station = nearby_ends.iloc[0]
        start_point = (start_station["from_station_lat"], start_station["from_station_lng"])
        end_point = (end_station["to_station_lat"], end_station["to_station_lng"])

        try:
            walk_to = self.otp_client.fastest_connection(when, start_coord, start_point)["duration"]
            walk_from = self.otp_client.fastest_connection(when, end_point, end_coord)["duration"]
        except Exception:
            walk_to = walk_from = 0

        dist_km = geodesic(start_point, end_point).km
        avg_bike_speed_kmh = 15.0
        bike_duration = (dist_km / avg_bike_speed_kmh) * 60
        total_combo = (walk_to + walk_from) / 60 + bike_duration

        return {
            "otp_duration_min": otp_duration / 60,
            "bike_distance_km": dist_km,
            "walk_to_bike_min": walk_to / 60,
            "walk_from_bike_min": walk_from / 60,
            "bike_duration_min": bike_duration,
            "total_bike_combo_min": total_combo,
            "start_station": start_station["from_station"],
            "end_station": end_station["to_station"]
        }

    def compare_as_dataframe(self, start_coord: Coord, end_coord: Coord, when: datetime):
        summary = self.compare_summary(start_coord, end_coord, when)
        return pd.DataFrame([summary])

    def draw_and_save_map_png(self, start_coord: Coord, end_coord: Coord, when: datetime, output_file="map.png"):
        summary = self.compare_summary(start_coord, end_coord, when)
        otp_itinerary = self.otp_client.fastest_connection(when, start_coord, end_coord)

        # Lista wszystkich punktów trasy do fit_bounds
        all_coords = []
        for leg in otp_itinerary["legs"]:
            frm, to = leg["from"], leg["to"]
            all_coords.append((frm["lat"], frm["lon"]))
            all_coords.append((to["lat"], to["lon"]))

        m = folium.Map(location=start_coord, zoom_start=13)  # zoom_start nieistotny jeśli fit_bounds

        # Rysuj całą trasę OTP
        for leg in otp_itinerary["legs"]:
            frm, to = leg["from"], leg["to"]
            folium.PolyLine(
                [(frm["lat"], frm["lon"]), (to["lat"], to["lon"])],
                color="blue", weight=5, opacity=0.5,
                tooltip=f"{leg['mode']}: {frm['name']} → {to['name']}"
            ).add_to(m)

        if "note" not in summary and "error" not in summary:
            start_point = (
                self.from_stations[self.from_stations["from_station"] == summary["start_station"]].iloc[0]["from_station_lat"],
                self.from_stations[self.from_stations["from_station"] == summary["start_station"]].iloc[0]["from_station_lng"]
            )
            end_point = (
                self.to_stations[self.to_stations["to_station"] == summary["end_station"]].iloc[0]["to_station_lat"],
                self.to_stations[self.to_stations["to_station"] == summary["end_station"]].iloc[0]["to_station_lng"]
            )

            all_coords.extend([start_point, end_point, start_coord, end_coord])

            folium.Marker(start_point, popup="Start roweru", icon=folium.Icon(color="green")).add_to(m)
            folium.Marker(end_point, popup="Koniec roweru", icon=folium.Icon(color="darkred")).add_to(m)
            folium.PolyLine([start_coord, start_point], color="gray", weight=2, dash_array="4,4").add_to(m)
            folium.PolyLine([start_point, end_point], color="purple", weight=4,
                            tooltip=f"Rower: {summary['bike_duration_min']:.1f} min").add_to(m)
            folium.PolyLine([end_point, end_coord], color="gray", weight=2, dash_array="4,4").add_to(m)

        # fit_bounds na całość trasy (najlepszy zoom!)
        if all_coords:
            m.fit_bounds(all_coords)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmpfile:
            html_file = tmpfile.name
        m.save(html_file)

        options = Options()
        options.headless = True
        options.add_argument("--window-size=1200,800")  # Zmień, jeśli chcesz większy obrazek!
        driver = webdriver.Chrome(options=options)
        driver.get("file://" + os.path.abspath(html_file))
        time.sleep(5)  # Daj czas na załadowanie mapy!
        driver.save_screenshot(output_file)
        driver.quit()