from pymongo import MongoClient
from domain.models import User


def get_users(user: User, client: MongoClient):
    db = client["trekDB"]
    collection = db["user"]
    filter = {"name": user.name, "email": user.email}
    update = {"$set": {"Perference": {}, "favorite_route": [], "places_history": {}}}

    a = collection.find_one_and_update(filter, update, upsert=True)
    return a
