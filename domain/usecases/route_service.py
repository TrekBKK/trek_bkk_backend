from fastapi import HTTPException
from pymongo import MongoClient


def edited(data, client: MongoClient):
    db = client.trekDB
    collection = db.editedRoute

    try:
        collection.insert_one(data)
        {"message": "history added successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
