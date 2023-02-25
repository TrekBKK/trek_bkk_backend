from fastapi import APIRouter, Depends, responses


from pymongo import MongoClient

from adapters import get_mongo_client

from domain.models import User
from domain.usecases import user_service

router = APIRouter(prefix="/user")


@router.get("/")
async def get_users():
    return "asd"


@router.post("/")
def temp(user: User, client: MongoClient = Depends(get_mongo_client)):
    a = user_service.get_users(user, client)
    a["_id"] = str(a["_id"])

    return responses.JSONResponse(content=a)
