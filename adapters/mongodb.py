from pymongo import MongoClient


def get_mongo_client():
    mongo_client = MongoClient("mongodb://localhost:27017")
    return mongo_client
