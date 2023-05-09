from datetime import datetime
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


def find_all_by_user_id(user_id: str, client: MongoClient):
    db = client.trekDB
    collection = db.proposeRoute

    try:
        query = {"user_id": user_id}

        results = collection.aggregate(
            [
                {"$match": query},
                {"$sort": {"_id": -1}},
                {"$addFields": {"timestamp": {"$toDate": "$_id"}}},
                {"$project": {"_id": 0}},
            ]
        )
        results_list = list(results)

        results_with_date = [
            {**result, "timestamp": result.get("timestamp").strftime("%d/%m/%y")}
            for result in results_list
        ]

        return results_with_date

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
