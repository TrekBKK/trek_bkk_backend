# ไม่ได้ login rating recommendation flow

# -nearby search/filter ตาม input
# -calculate distance metrix
# -sort nearby search result by rating, num_of_ratings equation
# -using distance metrix ถ้าใกล้กันเกินไม่เอา
# -เท่ากับ num stops: break return

import json
import os
import requests
from dotenv import load_dotenv
from math import radians, sin, cos, atan2, sqrt, log

load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two coordinates using the Spherical Law of Cosines.
    """
    R = 6373.0  # radius of the Earth in km

    lat1_rad = radians(lat1)
    lon1_rad = radians(lon1)
    lat2_rad = radians(lat2)
    lon2_rad = radians(lon2)

    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad

    a = sin(dlat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = R * c

    return distance


def nearby_search(src_id: str, dest_id: str, stops: int, tags: list[str]):
    src = requests.get(
        "https://maps.googleapis.com/maps/api/place/details/json",
        params={"fields": "geometry", "place_id": src_id, "key": API_KEY},
    ).json()["result"]["geometry"]["location"]

    dest = requests.get(
        "https://maps.googleapis.com/maps/api/place/details/json",
        params={"fields": "geometry", "place_id": dest_id, "key": API_KEY},
    ).json()["result"]["geometry"]["location"]

    # calculate the middle point between start and end points in degrees
    mid_lat = (src["lat"] + dest["lat"]) / 2
    mid_lng = (src["lng"] + dest["lng"]) / 2

    # calculate the distance between the middle point and each of the start and end points
    d_start = calculate_distance(src["lat"], src["lng"], mid_lat, mid_lng)
    d_end = calculate_distance(dest["lat"], dest["lng"], mid_lat, mid_lng)

    # choose the maximum distance as the radius
    radius = max(d_start, d_end)

    # Convert to meter &
    # multiply by radius factor to extend the coverage beyond starting and ending points
    radius = radius * 1000 * 1.1

    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    payload = {
        "location": f"{str(mid_lat)},{str(mid_lng)}",
        "radius": radius,
        "key": API_KEY,
    }

    raw = []
    res = requests.Response()

    if tags:
        for tag in tags:
            payload["type"] = tag

            res = requests.get(
                url,
                params=payload,
            )

            raw = raw + res.json()["results"]

    else:
        res = requests.get(
            url,
            params=payload,
        )

        raw = res.json()["results"]

    while len(raw) < 60 and res.json().get("next_page_token"):
        res = requests.get(
            url,
            params={"pagetoken": res.json()["next_page_token"]},
        )

        raw = raw + res.json()["results"]

    unique_places = {}

    for place in raw:
        json_str = json.dumps(place, sort_keys=True)
        unique_places[json_str] = place

    places = list(unique_places.values())

    # Calculate distances between all pairs of places
    distances = {}
    for i in range(len(places)):
        for j in range(i + 1, len(places)):
            dist = calculate_distance(
                places[i]["geometry"]["location"]["lat"],
                places[i]["geometry"]["location"]["lng"],
                places[j]["geometry"]["location"]["lat"],
                places[j]["geometry"]["location"]["lng"],
            )
            distances[(i, j)] = dist
            distances[(j, i)] = dist

    # Add index, Replace missing rating field with 0
    for i, place in enumerate(places):
        place["rating"] = place.get("rating", 0)
        place["user_ratings_total"] = place.get("user_ratings_total", 0)
        place["index"] = i

    # Set threshold distance for places to be considered too close
    threshold_distance = 0.2  # in km

    max_rating = 5
    max_user_ratings_total = max([place["user_ratings_total"] for place in places])

    # Rank using weighted sum + log + penalty
    places_sorted = sorted(
        places,
        key=lambda x: (
            (0.97 * x["rating"] / max_rating)
            * (0.5 if x["user_ratings_total"] < 20 else 1)
        )
        + (
            0.03
            * x["user_ratings_total"]
            / max_user_ratings_total
            * log(x["user_ratings_total"] + 1)
        ),
        reverse=True,
    )

    # Initialize list of recommended places
    recommended_places = []

    # Unqualified places and index for edit route
    unqualified = []
    index = 0

    # Iterate over ranked places and exclude those that are too close to previously recommended places
    for i, place in enumerate(places_sorted):
        if len(recommended_places) == stops:
            index = i
            break
        if not recommended_places:
            recommended_places.append(place)
        else:
            close_distances = [
                distances[(place["index"], rec_place["index"])] < threshold_distance
                for rec_place in recommended_places
            ]
            if not any(close_distances):
                recommended_places.append(place)
            else:
                unqualified.append(place)

    recommended_places.extend(unqualified)

    while len(recommended_places) < 20:
        recommended_places.append(places_sorted[index])
        index += 1

    return {"results": recommended_places, "routeIndex": stops + 2}
