from pymongo import MongoClient


def get_routes_for_home(client: MongoClient):
    db = client.trekDB
    collection = db.routes

    routes = collection.find({})

    list_routes = list(routes)

    for route in list_routes:
        route["_id"] = str(route["_id"])

    return list_routes
