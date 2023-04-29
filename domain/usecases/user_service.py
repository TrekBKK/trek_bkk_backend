from bson import ObjectId
from fastapi import HTTPException
from pymongo import MongoClient
from domain.models import User


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
    db = client["trekDB"]
    col_user = db["user"]
    col_route = db["routes"]
    try:
        doc_user = col_user.find_one(
            {"name": user.name, "email": user.email}, {"favorite_route": 1, "_id": 0})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        favorite_route_ids = doc_user["favorite_route"]

        # Look up routes by id
        favorite_routes = []
        for route_id in favorite_route_ids:
            route = col_route.find_one({"_id": ObjectId(route_id)})
            if route:
                route["_id"] = str(route["_id"])
                favorite_routes.append(route)

        return favorite_routes
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def get_history_routes(user: User, client: MongoClient):
    db = client["trekDB"]
    col_user = db["user"]
    col_route = db["routes"]
    try:
        doc_user = col_user.find_one(
            {"name": user.name, "email": user.email}, {"history_route": 1, "_id": 0})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        history_route_ids = doc_user["history_route"]

        # Look up routes by id
        history_routes = []
        for route_id in history_route_ids:
            route = col_route.find_one({"_id": ObjectId(route_id)})
            if route:
                route["_id"] = str(route["_id"])
                history_routes.append(route)

        return history_routes
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
