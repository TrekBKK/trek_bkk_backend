
from pymongo import MongoClient


def find_all_routes(searchKey: str, client: MongoClient):
    db = client.trekDB
    collection = db.routes

    filter = {"$text": {"$search": searchKey}}
    projection = {"_id": False}

    routes = collection.find(filter, projection)

    return list(routes)
