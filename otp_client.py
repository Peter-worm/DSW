from datetime import datetime
from typing import Any, List, Tuple

import requests

Coord = Tuple[float, float]  # (lat, lon)


class OTPClient:
    """
    Tiny wrapper around the OTP *GraphQL* endpoint.

    Parameters
    ----------
    graphql_url : str
        Default is the GTFS GraphQL API shipped with OTP ≥2.2:
        "http://localhost:8080/otp/gtfs/v1"  :contentReference[oaicite:0]{index=0}
    """

    def __init__(self, graphql_url: str = "http://localhost:8080/otp/gtfs/v1") -> None:
        self.url = graphql_url.rstrip("/")

    # ──────────────────────  public API  ──────────────────────
    def fastest_connection(
        self,
        when: datetime,
        start: Coord,
        end: Coord,
        *,
        n_itineraries: int = 5,
        search_window: str = "PT8H",
    ) -> dict[str, Any]:
        """Return the quickest itinerary departing **not before** *when*."""
        query = """
        query (
          $origin:       PlanLabeledLocationInput!,
          $destination:  PlanLabeledLocationInput!,
          $dateTime:     PlanDateTimeInput!,
          $first:        Int!,
          $searchWindow: Duration!
        ) {
          planConnection(
            origin:        $origin,
            destination:   $destination,
            dateTime:      $dateTime,
            first:         $first,
            searchWindow:  $searchWindow
          ) {
            edges {
              node {
                duration
                legs {
                  mode
                  startTime
                  endTime
                  from { lat lon name }
                  to   { lat lon name }
                }
              }
            }
            routingErrors { code description }
          }
        }
        """

        def loc(coord: Coord) -> dict[str, Any]:
            """PlanLabeledLocationInput for a raw (lat, lon) tuple."""
            return {
                "location": {
                    "coordinate": {
                        "latitude": coord[0],
                        "longitude": coord[1],
                    }
                }
            }

        variables = {
            "origin": loc(start),
            "destination": loc(end),
            "dateTime": {"earliestDeparture": when.astimezone().isoformat()},
            "first": n_itineraries,
            "searchWindow": search_window,
        }

        r = requests.post(
            self.url, json={"query": query, "variables": variables}, timeout=30
        )
        r.raise_for_status()
        data = r.json()

        if "errors" in data:
            raise RuntimeError(data["errors"])

        edges: List[dict] = data["data"]["planConnection"]["edges"]
        if not edges:
            raise ValueError("OTP returned no itineraries")

        itineraries = [e["node"] for e in edges]
        return min(itineraries, key=lambda it: it["duration"])


if __name__ == "__main__":
    PKP_GOLABKI = (52.208074, 20.864910)
    PLAC_POLITECHNIKI = (52.219916, 21.011682)

    when = (
        datetime.now().astimezone().replace(hour=12, minute=0, second=0, microsecond=0)
    )

    otp = OTPClient()  # defaults to http://localhost:8080/otp/gtfs/v1
    itinerary = otp.fastest_connection(when, PKP_GOLABKI, PLAC_POLITECHNIKI)

    mins, secs = divmod(itinerary["duration"], 60)
    print(
        f"Fastest trip takes {int(mins)} min {int(secs)} s across"
        f" {len(itinerary['legs'])} legs."
    )

    for leg in itinerary["legs"]:
        frm, to = leg["from"], leg["to"]
        print(
            f"{leg['mode']:7s}"
            f" {frm['lat']:.5f},{frm['lon']:.5f} → {to['lat']:.5f},{to['lon']:.5f}"
        )
