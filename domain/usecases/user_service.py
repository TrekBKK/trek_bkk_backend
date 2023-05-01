from bson import ObjectId
from fastapi import HTTPException
from pymongo import MongoClient
from domain.models import User
import requests
from dotenv import load_dotenv
import os

load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")


def get_user(user: User, client: MongoClient):
    db = client["trekDB"]
    collection = db["user"]
    try:
        _user = collection.find_one({"name": user.name, "email": user.email})
        if _user:
            return _user
        print(user.name, user.photo)
        userData = {"name": user.name, "email": user.email, "photo": user.photo,
                    "perference": False, "favorite_route": [], "places_history": []}
        _id = collection.insert_one(userData).inserted_id
        userData["_id"] = _id
        return userData

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def get_favorite_routes(user: User, client: MongoClient):
    db = client.trekDB
    col_route = db.routes
    col_user = db.user

    try:
        doc_user = col_user.find_one(
            {"name": user.name, "email": user.email}, {"favorite_route": 1, "_id": 0})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        favorite_route_ids = doc_user["favorite_route"]

        query = {"_id": {"$in": [ObjectId(id) for id in favorite_route_ids]}}
        projection = {"_id": False}
        favorite_routes = col_route.find(query, projection)
        routes = list(favorite_routes)

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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def get_history_routes(user: User, client: MongoClient):
    db = client.trekDB
    col_route = db.routes
    col_user = db.user
    res = []

    try:
        doc_user = col_user.find_one(
            {"name": user.name, "email": user.email}, {"history_route": 1, "_id": 0})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        routes = doc_user["history_route"]
        route_ids = [subdocument.pop("route_id") for subdocument in routes]
        query = {"_id": {"$in": [ObjectId(id) for id in route_ids]}}
        projection = {"_id": False}

        history_routes = list(col_route.find(query, projection))
        url = "https://maps.googleapis.com/maps/api/place/details/json?"
        for route in history_routes:
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

        for i in range(len(routes)):
            routes[i]["route"] = history_routes[i]

        return routes
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
