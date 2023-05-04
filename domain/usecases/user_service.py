from bson import ObjectId
from fastapi import HTTPException
from pymongo import MongoClient, ReturnDocument
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
                    "preference": {"distance": "",
                                   "stop": "",
                                   "type": []}, "favorite_route": [], "history_route": []}
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
        favorite_routes = col_route.find(query)
        routes = list(favorite_routes)

        url = "https://maps.googleapis.com/maps/api/place/details/json?"
        for route in routes:
            route["_id"] = str(route["_id"])
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


def update_favorite_routes(user_id, route_id, client: MongoClient):
    db = client.trekDB
    col_user = db.user

    try:
        document = col_user.find_one({'_id': ObjectId(user_id)})
        if document is None:
            return {'message': 'Document not found.'}
        favorite_route = document.get('favorite_route', [])
        if route_id in favorite_route:
            favorite_route.remove(route_id)
        else:
            favorite_route.append(route_id)
        col_user.update_one({'_id': ObjectId(user_id)}, {
                            '$set': {'favorite_route': favorite_route}})
        return {'message': 'Favorite route updated successfully.'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def update_user_pref(user: User, client: MongoClient):
    db = client.trekDB
    col_user = db.user
    try:
        preference_data = {
            "distance": user.preference["distance"],
            "stop": user.preference["stop"],
            "type": user.preference["type"]
        }
        query = {"name": user.name}
        update = {"$set": {"preference": preference_data}}
        user = col_user.find_one_and_update(
            query,
            update,
            return_document=ReturnDocument.AFTER
        )
        if user:
            return {"message": "Preference updated successfully"}
        else:
            raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def get_history_routes(user: User, client: MongoClient):
    db = client.trekDB
    col_route = db.routes
    col_user = db.user

    try:
        doc_user = col_user.find_one(
            {"name": user.name, "email": user.email}, {"history_route": 1, "_id": 0})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        routes = doc_user["history_route"]
        route_ids = [subdocument.pop("route_id") for subdocument in routes]
        query = {"_id": {"$in": [ObjectId(id) for id in route_ids]}}

        history_routes = list(col_route.find(query, ))
        url = "https://maps.googleapis.com/maps/api/place/details/json?"
        for route in history_routes:
            route["_id"] = str(route["_id"])
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
