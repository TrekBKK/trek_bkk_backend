from fastapi import HTTPException
from pymongo import MongoClient
from domain.models import ProposeInput


def propose(route: ProposeInput, client: MongoClient):
    db = client.trekDB
    collection = db.proposeRoute

    try:
        _id = collection.insert_one(route.dict()).inserted_id
        return str(_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
