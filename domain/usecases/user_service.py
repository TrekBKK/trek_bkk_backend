from bson import ObjectId
from fastapi import HTTPException
from pymongo import MongoClient
from domain.models import User


def get_users(user: User, client: MongoClient):
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
