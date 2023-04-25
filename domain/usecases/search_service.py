import requests
import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")


def find_all_by_key(searchKey: str, client: MongoClient):
    db = client.trekDB
    collection = db.routes

    filter = {"$text": {"$search": searchKey}}
    projection = {"_id": False}

    routes = collection.find(filter, projection)

    routes = list(routes)

    url = "https://maps.googleapis.com/maps/api/place/details/json?"

    for route in routes:
        waypoints = []
        for waypoint in route["geocoded_waypoints"]:
            r = requests.get(
                url,
                params={
                    "place_id": waypoint["place_id"],
                    "fields": "place_id,name,geometry,types",
                    "key": API_KEY,
                },
            )

            result = r.json()["result"]

            waypoints.append(result)

        route["geocoded_waypoints"] = waypoints

    return routes


def find_all_by_places(
    src_id: str | None,
    dest_id: str | None,
    place_ids: list[str] | None,
    client: MongoClient,
):
    db = client.trekDB
    collection = db.routes

    filter = {
        "geocoded_waypoints.0.place_id": src_id or {"$exists": True},
        "$expr": {
            "$eq": [{"$arrayElemAt": ["$geocoded_waypoints.place_id", -1]}, dest_id]
        }
        if dest_id
        else True,
        "geocoded_waypoints.place_id": {"$all": place_ids}
        if place_ids
        else {"$exists": True},
    }
    projection = {"_id": False}

    routes = collection.find(filter, projection)

    routes = list(routes)

    url = "https://maps.googleapis.com/maps/api/place/details/json?"

    for route in routes:
        waypoints = []
        for waypoint in route["geocoded_waypoints"]:
            r = requests.get(
                url,
                params={
                    "place_id": waypoint["place_id"],
                    "fields": "place_id,name,geometry,types",
                    "key": API_KEY,
                },
            )

            result = r.json()["result"]

            waypoints.append(result)

        route["geocoded_waypoints"] = waypoints

    return routes
