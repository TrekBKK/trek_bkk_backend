from pymongo import MongoClient


def get_mongo_client():
    mongo_client = MongoClient(
        "mongodb+srv://trek:trek123bkk@trekcluster.gpygzfw.mongodb.net/?retryWrites=true&w=majority"
    )
    return mongo_client
